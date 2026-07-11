from contextlib import asynccontextmanager
from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel
from .authentication import SESSION_COOKIE, authenticate, identity, resolve_session, revoke_session
from .authorization import ForbiddenError, ResourceKind, ResourceScope, Action, require_permission
from .ingestion import InvalidUpload, create_upload_job, list_jobs
from .runtime import ensure_bucket, readiness

@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_bucket()
    yield

app = FastAPI(title="ContractView POC API", version="0.1.0", lifespan=lifespan)

class LoginRequest(BaseModel):
    email: str
    password: str

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
    dependencies = readiness()
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

@app.post("/demo/configuration/activate")
def protected_activation(resolved=Depends(current_identity)):
    actor, _ = resolved
    resource = ResourceScope("demo-configuration", ResourceKind.CONFIGURATION, actor.organization_id)
    try:
        require_permission(actor, Action.ACTIVATE, resource)
    except ForbiddenError as error:
        raise HTTPException(status_code=403, detail="Permission denied") from error
    return {"allowed": True}

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
