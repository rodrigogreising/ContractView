import json,uuid
from .attestation import current_attestation
from .access_scope import invoice_scope
from ...authorization import Action,Actor,execute_authorized
from .provenance import append_event_tx, append_relation_tx
from .invoice_snapshots import create_invoice_snapshot_tx

from ..ports.statements import Statement
from ..transaction import transaction as database
class SubmissionError(ValueError):pass

def submit(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        invoice=connection.invoices.execute(Statement.SUBMISSION_READ_INVOICE_VERSIONS_001,(invoice_id,)).fetchone()
    if not invoice:raise FileNotFoundError(invoice_id)
    scope=invoice_scope(actor,invoice_id)
    def command():
        att=current_attestation(actor,invoice_id)
        if invoice[4]!="draft":raise SubmissionError("Only a draft version may be submitted")
        if not att or not att["current"]:raise SubmissionError("A current attestation is required")
        with database() as connection:
            package=connection.packages.execute(Statement.SUBMISSION_READ_PACKAGES_002,(invoice_id,att["id"])).fetchone()
            if not package:raise SubmissionError("Generate the attested package before submission")
            hashes=connection.packages.execute(Statement.SUBMISSION_READ_PACKAGE_ARTIFACTS_003,(package[0],)).fetchall()
            submission_id=f"submission-{uuid.uuid4().hex}";queue_id=f"queue-{uuid.uuid4().hex}"
            contract=connection.configuration.execute(Statement.SUBMISSION_READ_CONTRACTS_004,(invoice[1],)).fetchone()
            connection.invoices.execute(Statement.SUBMISSION_WRITE_INVOICE_VERSIONS_007,(invoice_id,))
            snapshot=create_invoice_snapshot_tx(connection,actor,invoice_id,"submission")
            connection.workflow.execute(Statement.SUBMISSION_WRITE_SUBMISSIONS_005,(submission_id,invoice_id,package[0],actor.user_id,actor.role.value,invoice[2],invoice[3],json.dumps(dict(hashes)),snapshot["id"]))
            append_relation_tx(connection,invoice[1],invoice[0],"submitted_as",
                {"kind":"invoice_snapshot","id":snapshot["id"],"version":snapshot["payload"]["materialRevision"],"sha256":snapshot["sha256"]},
                {"kind":"submission","id":submission_id,"version":invoice[3]},actor=actor)
            connection.workflow.execute(Statement.SUBMISSION_WRITE_GOVERNMENT_QUEUE_ITEMS_006,(queue_id,submission_id,contract[0],contract[1]))
            artifact_rows=connection.read_models.execute(Statement.SUBMISSION_READ_EXTRACTION_FIELDS_EXTRACTION_FIELDS_EXTRACTION_RUNS_EXTRACTION_RUNS_008,(package[0],invoice_id,invoice_id,invoice_id,invoice_id)).fetchall()
            is_resubmission=bool(connection.invoices.execute(
                Statement.SUBMISSION_READ_INVOICE_VERSION_LINKS_010,(invoice_id,)
            ).fetchone()[0])
            artifact_ids=[row[0] for row in artifact_rows]
            if artifact_ids:
                connection.artifacts.execute(Statement.SUBMISSION_WRITE_ARTIFACTS_009,(artifact_ids,))
            append_event_tx(connection,"resubmitted" if is_resubmission else "submitted","invoice_version",invoice_id,actor_id=actor.user_id,organization_id=invoice[0],contract_id=invoice[1],payload={"submissionId":submission_id,"queueItemId":queue_id,"packageId":package[0],"invoiceVersion":invoice[3],"configurationVersionId":invoice[2],"packageHashes":dict(hashes),"invoiceSnapshotId":snapshot["id"]},version_references=[
                {"kind":"submission","id":submission_id,"version":invoice[3]},
                {"kind":"invoice_snapshot","id":snapshot["id"],"version":snapshot["payload"]["materialRevision"],"sha256":snapshot["sha256"]},
                {"kind":"invoice","id":invoice_id,"version":invoice[3]},
                {"kind":"package","id":package[0],"version":invoice[3]},
                {"kind":"configuration","id":invoice[2],"version":invoice[2]},
            ]);connection.commit()
        return {"id":submission_id,"invoiceVersionId":invoice_id,"packageId":package[0],"queueItemId":queue_id,"invoiceVersion":invoice[3],"configurationVersionId":invoice[2],"packageHashes":dict(hashes),"state":"submitted"}
    return execute_authorized(actor,Action.SUBMIT,scope,command)
