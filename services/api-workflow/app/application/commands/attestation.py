from hashlib import sha256
import json
import uuid

from .access_scope import invoice_scope
from ...authorization import Action,Actor,execute_authorized,require_permission
from .finding_resolution import current_findings,has_open_blockers
from .invoice_draft import get_draft
from .invoice_snapshots import create_invoice_snapshot_tx
from .provenance import append_event_tx

from ..ports.statements import Statement
from ..transaction import transaction as database
ATTESTATION_VERSION="ngo-approver-attestation-v1"
ATTESTATION_TEXT="I attest that I reviewed this exact invoice version, its evidence, validation results, and configuration, and authorize package generation for submission."

class AttestationError(ValueError):pass

def _canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),default=str)

def invoice_fingerprint(invoice_id:str,validation_run_id:str)->str:
    with database() as connection:
        invoice=connection.invoices.execute(Statement.ATTESTATION_READ_INVOICE_VERSIONS_001,(invoice_id,)).fetchone()
        lines=connection.invoices.execute(Statement.ATTESTATION_READ_INVOICE_LINES_002,(invoice_id,)).fetchall()
        hashes=connection.read_models.execute(Statement.ATTESTATION_READ_ARTIFACTS_INVOICE_LINES_INVOICE_LINES_003,(invoice_id,invoice_id)).fetchall()
        validation=connection.validation.execute(Statement.ATTESTATION_READ_VALIDATION_RUNS_004,(validation_run_id,)).fetchone()
    return sha256(_canonical({"invoice":invoice,"lines":lines,"artifacts":hashes,"validation":validation}).encode()).hexdigest()

def approval_preview(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        invoice=connection.invoices.execute(Statement.ATTESTATION_READ_INVOICE_VERSIONS_005,(invoice_id,)).fetchone()
        if not invoice:raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,invoice_scope(actor,invoice_id))
        run=connection.validation.execute(Statement.ATTESTATION_READ_VALIDATION_RUNS_006,(invoice_id,)).fetchone()
        evidence_row=connection.invoices.execute(Statement.ATTESTATION_READ_INVOICE_LINES_007,(invoice_id,)).fetchone()
        if not evidence_row:raise RuntimeError("Invoice evidence count is missing")
        evidence_count=evidence_row[0]
    draft=get_draft(actor,invoice_id);findings=current_findings(actor,invoice_id)
    fresh=bool(run and run[2]==invoice[1])
    return {"invoice":draft,"validationRunId":run[0] if run else None,"validationOutputHash":run[1] if run else None,"validationFresh":fresh,"materialRevision":invoice[1],"findings":findings,"hasOpenBlockers":has_open_blockers(invoice_id),"packagePreview":{"files":["invoice.pdf","validation-summary.json","manifest.json","manifest.csv",f"evidence/{evidence_count}-supporting-files","package.zip"],"evidenceCount":evidence_count},"attestationVersion":ATTESTATION_VERSION,"attestationText":ATTESTATION_TEXT}

def attest(actor:Actor,invoice_id:str,text:str)->dict:
    with database() as connection:
        invoice=connection.invoices.execute(Statement.ATTESTATION_READ_INVOICE_VERSIONS_008,(invoice_id,)).fetchone()
    if not invoice:raise FileNotFoundError(invoice_id)
    def command():
        if invoice[1]!="draft":raise AttestationError("Only a draft invoice may be attested")
        if text!=ATTESTATION_TEXT:raise AttestationError("The exact attestation text is required")
        preview=approval_preview(actor,invoice_id)
        if not preview["validationFresh"]:raise AttestationError("Run fresh validation after the latest material change")
        if preview["hasOpenBlockers"]:raise AttestationError("Resolve all blockers before attestation")
        fingerprint=invoice_fingerprint(invoice_id,preview["validationRunId"]);attestation_id=f"attestation-{uuid.uuid4().hex}"
        with database() as connection:
            snapshot=create_invoice_snapshot_tx(connection,actor,invoice_id,"attestation")
            connection.workflow.execute(Statement.ATTESTATION_WRITE_ATTESTATIONS_009,(attestation_id,invoice_id,preview["validationRunId"],preview["materialRevision"],fingerprint,actor.user_id,actor.role.value,ATTESTATION_VERSION,text,snapshot["id"]))
            contract=connection.invoices.execute(Statement.ATTESTATION_READ_INVOICE_VERSIONS_010,(invoice_id,)).fetchone()[0]
            append_event_tx(connection,"attested","invoice_version",invoice_id,actor_id=actor.user_id,organization_id=invoice[0],contract_id=contract,payload={"attestationId":attestation_id,"validationRunId":preview["validationRunId"],"materialRevision":preview["materialRevision"],"fingerprint":fingerprint,"attestationVersion":ATTESTATION_VERSION,"invoiceSnapshotId":snapshot["id"]},version_references=[
                {"kind":"invoice_snapshot","id":snapshot["id"],"version":preview["materialRevision"],"sha256":snapshot["sha256"]},
                {"kind":"invoice","id":invoice_id,"version":snapshot["payload"]["invoiceVersion"]},
                {"kind":"validation_run","id":preview["validationRunId"],"version":1},
            ])
            connection.commit()
        return current_attestation(actor,invoice_id)
    return execute_authorized(actor,Action.ATTEST,invoice_scope(actor,invoice_id),command)

def current_attestation(actor:Actor,invoice_id:str)->dict|None:
    with database() as connection:
        invoice=connection.invoices.execute(Statement.ATTESTATION_READ_INVOICE_VERSIONS_011,(invoice_id,)).fetchone()
        if not invoice:raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,invoice_scope(actor,invoice_id))
        row=connection.workflow.execute(Statement.ATTESTATION_READ_ATTESTATIONS_012,(invoice_id,)).fetchone()
    if not row:return None
    current=row[2]==invoice[1] and row[3]==invoice_fingerprint(invoice_id,row[1])
    return {"id":row[0],"invoiceVersionId":invoice_id,"validationRunId":row[1],"materialRevision":row[2],"fingerprint":row[3],"actorId":row[4],"actorRole":row[5],"attestationVersion":row[6],"attestationText":row[7],"createdAt":row[8].isoformat(),"current":current}
