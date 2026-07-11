from hashlib import sha256
import json
import uuid

from .authorization import Action,Actor,ResourceKind,ResourceScope,execute_authorized,require_permission
from .finding_resolution import current_findings,has_open_blockers
from .invoice_draft import get_draft
from .provenance import append_event_tx
from .runtime import database

ATTESTATION_VERSION="ngo-approver-attestation-v1"
ATTESTATION_TEXT="I attest that I reviewed this exact invoice version, its evidence, validation results, and configuration, and authorize package generation for submission."

class AttestationError(ValueError):pass

def _scope(invoice_id,org):return ResourceScope(invoice_id,ResourceKind.INVOICE,org,ngo_organization_id=org)
def _canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),default=str)

def invoice_fingerprint(invoice_id:str,validation_run_id:str)->str:
    with database() as connection:
        invoice=connection.execute("select configuration_version_id,material_revision,total from invoice_versions where id=%s",(invoice_id,)).fetchone()
        lines=connection.execute("""select expense_key,expense_date,budget_category,claimed_amount,ledger_artifact_id,evidence_artifact_id,extraction_status
                                   from invoice_lines where invoice_version_id=%s order by expense_key""",(invoice_id,)).fetchall()
        hashes=connection.execute("""select a.id,a.sha256 from artifacts a where a.id in
                                     (select ledger_artifact_id from invoice_lines where invoice_version_id=%s union select evidence_artifact_id from invoice_lines where invoice_version_id=%s) order by a.id""",(invoice_id,invoice_id)).fetchall()
        validation=connection.execute("select input_hash,output_hash,material_revision from validation_runs where id=%s",(validation_run_id,)).fetchone()
    return sha256(_canonical({"invoice":invoice,"lines":lines,"artifacts":hashes,"validation":validation}).encode()).hexdigest()

def approval_preview(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        invoice=connection.execute("select organization_id,material_revision,configuration_version_id from invoice_versions where id=%s",(invoice_id,)).fetchone()
        if not invoice:raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,_scope(invoice_id,invoice[0]))
        run=connection.execute("""select id,output_hash,material_revision,created_at from validation_runs
                                  where invoice_version_id=%s and engine_version is not null order by created_at desc,id desc limit 1""",(invoice_id,)).fetchone()
        evidence_count=connection.execute("select count(distinct evidence_artifact_id) from invoice_lines where invoice_version_id=%s and evidence_artifact_id is not null",(invoice_id,)).fetchone()[0]
    draft=get_draft(actor,invoice_id);findings=current_findings(actor,invoice_id)
    fresh=bool(run and run[2]==invoice[1])
    return {"invoice":draft,"validationRunId":run[0] if run else None,"validationOutputHash":run[1] if run else None,"validationFresh":fresh,"materialRevision":invoice[1],"findings":findings,"hasOpenBlockers":has_open_blockers(invoice_id),"packagePreview":{"files":["invoice.pdf","validation-summary.json","manifest.json","manifest.csv",f"evidence/{evidence_count}-supporting-files","package.zip"],"evidenceCount":evidence_count},"attestationVersion":ATTESTATION_VERSION,"attestationText":ATTESTATION_TEXT}

def attest(actor:Actor,invoice_id:str,text:str)->dict:
    with database() as connection:
        invoice=connection.execute("select organization_id,state,material_revision from invoice_versions where id=%s",(invoice_id,)).fetchone()
    if not invoice:raise FileNotFoundError(invoice_id)
    def command():
        if invoice[1]!="draft":raise AttestationError("Only a draft invoice may be attested")
        if text!=ATTESTATION_TEXT:raise AttestationError("The exact attestation text is required")
        preview=approval_preview(actor,invoice_id)
        if not preview["validationFresh"]:raise AttestationError("Run fresh validation after the latest material change")
        if preview["hasOpenBlockers"]:raise AttestationError("Resolve all blockers before attestation")
        fingerprint=invoice_fingerprint(invoice_id,preview["validationRunId"]);attestation_id=f"attestation-{uuid.uuid4().hex}"
        with database() as connection:
            connection.execute("""insert into attestations(id,invoice_version_id,validation_run_id,material_revision,invoice_fingerprint,actor_id,actor_role,attestation_version,attestation_text)
                                  values (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(attestation_id,invoice_id,preview["validationRunId"],preview["materialRevision"],fingerprint,actor.user_id,actor.role.value,ATTESTATION_VERSION,text))
            contract=connection.execute("select contract_id from invoice_versions where id=%s",(invoice_id,)).fetchone()[0]
            append_event_tx(connection,"attested","invoice_version",invoice_id,actor_id=actor.user_id,organization_id=invoice[0],contract_id=contract,payload={"attestationId":attestation_id,"validationRunId":preview["validationRunId"],"materialRevision":preview["materialRevision"],"fingerprint":fingerprint,"attestationVersion":ATTESTATION_VERSION})
            connection.commit()
        return current_attestation(actor,invoice_id)
    return execute_authorized(actor,Action.ATTEST,_scope(invoice_id,invoice[0]),command)

def current_attestation(actor:Actor,invoice_id:str)->dict|None:
    with database() as connection:
        invoice=connection.execute("select organization_id,material_revision from invoice_versions where id=%s",(invoice_id,)).fetchone()
        if not invoice:raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,_scope(invoice_id,invoice[0]))
        row=connection.execute("""select id,validation_run_id,material_revision,invoice_fingerprint,actor_id,actor_role,attestation_version,attestation_text,created_at
                                  from attestations where invoice_version_id=%s order by created_at desc,id desc limit 1""",(invoice_id,)).fetchone()
    if not row:return None
    current=row[2]==invoice[1] and row[3]==invoice_fingerprint(invoice_id,row[1])
    return {"id":row[0],"invoiceVersionId":invoice_id,"validationRunId":row[1],"materialRevision":row[2],"fingerprint":row[3],"actorId":row[4],"actorRole":row[5],"attestationVersion":row[6],"attestationText":row[7],"createdAt":row[8].isoformat(),"current":current}
