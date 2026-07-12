from contextlib import asynccontextmanager
from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import Response as BinaryResponse
from pydantic import BaseModel
from ..authentication import SESSION_COOKIE, authenticate, identity, resolve_session, revoke_session
from ..authorization import ForbiddenError
from ..ingestion import InvalidUpload, create_upload_job, list_jobs
from ..artifacts import download_artifact, get_artifact
from ..extraction_review import InvalidReview, list_extractions, review_field
from ..invoice_draft import DraftAssemblyError, assemble_draft, latest_draft
from ..configuration import (
    InvalidConfiguration,
    active_summary,
    activate_version,
    approve_version,
    get_draft,
    lifecycle_history,
    retire_version,
    rollback_version,
    supersede_version,
    test_draft,
    update_draft,
)
from ..validation import execute_validation,latest_validation
from ..budget import budget_snapshot
from ..finding_resolution import InvalidResolution,current_findings,resolve_finding
from ..attestation import ATTESTATION_TEXT,AttestationError,approval_preview,attest,current_attestation
from ..package_generation import PackageError,generate_package
from ..submission import SubmissionError,submit
from ..government_review import list_queue,review_context
from ..government_decision import DecisionError,decide
from ..revision import RevisionError,correct_revision,revision_feedback
from ..provenance import audit_timeline
from ..shared_contracts import AuditTimelineDto
from ..application.runtime_health import ensure_runtime_ready, runtime_readiness
from ..access_scope import contract_contexts

@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_ready()
    yield

app = FastAPI(title="ContractView POC API", version="0.1.0", lifespan=lifespan)

class LoginRequest(BaseModel):
    email: str
    password: str

class FieldReviewRequest(BaseModel):
    decision: str
    value: str | None = None
    reason: str | None = None

class FindingResolutionRequest(BaseModel):
    action: str
    reason: str
    correctionValue: str | None = None

class AttestationRequest(BaseModel):
    text: str
class GovernmentDecisionRequest(BaseModel):
    decision:str
    reasonCode:str
    note:str
    lineKeys:list[str]=[]
class RevisionCorrectionRequest(BaseModel):
    expenseKey:str
    description:str
    reason:str

class RationaleRequest(BaseModel):
    rationale: str

class ActivateConfigurationRequest(RationaleRequest):
    versionId: str

class SupersedeConfigurationRequest(RationaleRequest):
    successorVersionId: str

class RollbackConfigurationRequest(RationaleRequest):
    targetVersionId: str

def current_identity(contractview_session: str | None = Cookie(default=None)):
    resolved = resolve_session(contractview_session)
    if not resolved:
        raise HTTPException(status_code=401, detail="Authentication required")
    return resolved

@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "service": "api", "version": app.version}

@app.get("/health/ready")
def ready() -> dict[str, object]:
    dependencies = runtime_readiness()
    if not all(dependencies.values()):
        raise HTTPException(status_code=503, detail=dependencies)
    return {"status": "ready", "service": "api", "version": app.version, "dependencies": dependencies}

@app.post("/auth/login")
def login(payload: LoginRequest, response: Response):
    result = authenticate(payload.email, payload.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, actor, profile = result
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", secure=False, max_age=8 * 60 * 60, path="/")
    return {"user": identity(actor, profile)}

@app.post("/auth/logout", status_code=204)
def logout(response: Response, contractview_session: str | None = Cookie(default=None)):
    revoke_session(contractview_session)
    response.delete_cookie(SESSION_COOKIE, path="/")

@app.get("/auth/me")
def me(resolved=Depends(current_identity)):
    actor, profile = resolved
    return {"user": identity(actor, profile)}

@app.get("/auth/contracts")
def authorized_contracts(resolved=Depends(current_identity)):
    actor, _ = resolved
    return {"contracts": contract_contexts(actor)}

@app.get("/audit/timeline", response_model=AuditTimelineDto)
def read_audit_timeline(contractId: str, resolved=Depends(current_identity)):
    actor, _ = resolved
    try:
        return audit_timeline(actor, contractId)
    except ForbiddenError as error:
        raise HTTPException(status_code=403, detail="Permission denied") from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Contract not found") from error

@app.post("/ingestion/uploads", status_code=202)
async def upload_evidence(contractId: str = Form(...), file: UploadFile = File(...), resolved=Depends(current_identity)):
    actor, _ = resolved
    content = await file.read(10 * 1024 * 1024 + 1)
    try:
        job = create_upload_job(actor, contractId, file.filename or "upload", file.content_type or "", content)
    except InvalidUpload as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ForbiddenError as error:
        raise HTTPException(status_code=403, detail="Permission denied") from error
    return {"job": job.__dict__}

@app.get("/ingestion/jobs")
def ingestion_jobs(contractId: str, resolved=Depends(current_identity)):
    actor, _ = resolved
    try:
        return {"jobs": [job.__dict__ for job in list_jobs(actor, contractId)]}
    except ForbiddenError as error:
        raise HTTPException(status_code=403, detail="Permission denied") from error

@app.get("/extractions/review")
def extraction_review_queue(contractId: str, resolved=Depends(current_identity)):
    actor, _ = resolved
    try: return {"extractions": list_extractions(actor, contractId)}
    except ForbiddenError as error: raise HTTPException(status_code=403, detail="Permission denied") from error

@app.post("/extractions/fields/{field_id}/review")
def submit_field_review(field_id: str, payload: FieldReviewRequest, resolved=Depends(current_identity)):
    actor, _ = resolved
    try: return {"field": review_field(actor, field_id, payload.decision, payload.value, payload.reason)}
    except ForbiddenError as error: raise HTTPException(status_code=403, detail="Permission denied") from error
    except InvalidReview as error: raise HTTPException(status_code=422, detail=str(error)) from error

@app.get("/artifacts/{artifact_id}")
def artifact_download(artifact_id: str, resolved=Depends(current_identity)):
    actor, _ = resolved
    artifact = get_artifact(artifact_id)
    if not artifact: raise HTTPException(status_code=404, detail="Artifact not found")
    try: content = download_artifact(actor, artifact_id)
    except ForbiddenError as error: raise HTTPException(status_code=403, detail="Permission denied") from error
    return BinaryResponse(content=content,media_type=artifact.media_type,headers={"Content-Disposition":f'inline; filename="{artifact.filename}"'})

@app.post("/invoices/draft")
def create_invoice_draft(contractId: str, resolved=Depends(current_identity)):
    actor, _ = resolved
    try: return {"invoice":assemble_draft(actor,contractId)}
    except ForbiddenError as error: raise HTTPException(status_code=403,detail="Permission denied") from error
    except DraftAssemblyError as error: raise HTTPException(status_code=422,detail=str(error)) from error

@app.get("/invoices/draft")
def get_latest_invoice_draft(contractId: str, resolved=Depends(current_identity)):
    actor, _ = resolved
    try: return {"invoice":latest_draft(actor,contractId)}
    except ForbiddenError as error: raise HTTPException(status_code=403,detail="Permission denied") from error

@app.get("/configuration/draft")
def configuration_draft(contractId: str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configuration":get_draft(actor,contractId)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.put("/configuration/draft")
def save_configuration_draft(contractId: str,payload: dict,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configuration":update_draft(actor,contractId,payload)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/configuration/test")
def test_configuration(contractId: str,payload:RationaleRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configurationVersion":test_draft(actor,contractId,payload.rationale)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/configuration/versions/{version_id}/approve")
def approve_configuration(version_id:str,payload:RationaleRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configurationVersion":approve_version(actor,version_id,payload.rationale)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/configuration/activate")
def activate_configuration(payload:ActivateConfigurationRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configurationVersion":activate_version(actor,payload.versionId,payload.rationale)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/configuration/versions/{version_id}/supersede")
def supersede_configuration(version_id:str,payload:SupersedeConfigurationRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configurationVersion":supersede_version(actor,version_id,payload.successorVersionId,payload.rationale)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/configuration/versions/{version_id}/retire")
def retire_configuration(version_id:str,payload:RationaleRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configurationVersion":retire_version(actor,version_id,payload.rationale)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/configuration/rollback")
def rollback_configuration(contractId:str,payload:RollbackConfigurationRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configurationVersion":rollback_version(actor,contractId,payload.targetVersionId,payload.rationale)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.get("/configuration/lifecycle")
def configuration_lifecycle(contractId:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return lifecycle_history(actor,contractId)
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidConfiguration as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.get("/configuration/active")
def active_configuration(contractId: str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"configuration":active_summary(actor,contractId)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.post("/invoices/{invoice_id}/validation")
def run_validation(invoice_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"validation":execute_validation(actor,invoice_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.get("/invoices/{invoice_id}/validation")
def get_validation(invoice_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"validation":latest_validation(actor,invoice_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.get("/invoices/{invoice_id}/budget")
def invoice_budget(invoice_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"budget":budget_snapshot(actor,invoice_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.get("/invoices/{invoice_id}/findings")
def invoice_findings(invoice_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"findings":current_findings(actor,invoice_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.post("/findings/{finding_id}/resolve")
def submit_finding_resolution(finding_id:str,payload:FindingResolutionRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"resolution":resolve_finding(actor,finding_id,payload.action,payload.reason,payload.correctionValue)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except InvalidResolution as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.get("/invoices/{invoice_id}/approval-preview")
def get_approval_preview(invoice_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"preview":approval_preview(actor,invoice_id),"attestation":current_attestation(actor,invoice_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.post("/invoices/{invoice_id}/attest")
def attest_invoice(invoice_id:str,payload:AttestationRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"attestation":attest(actor,invoice_id,payload.text)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except AttestationError as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/invoices/{invoice_id}/package")
def generate_invoice_package(invoice_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"package":generate_package(actor,invoice_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except PackageError as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.post("/invoices/{invoice_id}/submit")
def submit_invoice(invoice_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"submission":submit(actor,invoice_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except SubmissionError as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.get("/government/queue")
def government_queue(resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"items":list_queue(actor)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.get("/government/queue/{queue_id}")
def government_review_context(queue_id:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"review":review_context(actor,queue_id)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except FileNotFoundError as error:raise HTTPException(status_code=404,detail="Queue item not found") from error

@app.post("/government/queue/{queue_id}/decision")
def government_decision(queue_id:str,payload:GovernmentDecisionRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"decision":decide(actor,queue_id,payload.decision,payload.reasonCode,payload.note,payload.lineKeys)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except DecisionError as error:raise HTTPException(status_code=422,detail=str(error)) from error

@app.get("/revisions/feedback")
def get_revision_feedback(contractId:str,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"feedback":revision_feedback(actor,contractId)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error

@app.post("/invoices/{invoice_id}/revision-correction")
def submit_revision_correction(invoice_id:str,payload:RevisionCorrectionRequest,resolved=Depends(current_identity)):
    actor,_=resolved
    try:return {"correction":correct_revision(actor,invoice_id,payload.expenseKey,payload.description,payload.reason)}
    except ForbiddenError as error:raise HTTPException(status_code=403,detail="Permission denied") from error
    except RevisionError as error:raise HTTPException(status_code=422,detail=str(error)) from error
