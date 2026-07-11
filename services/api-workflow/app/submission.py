import json,uuid
from .attestation import current_attestation
from .access_scope import invoice_scope
from .authorization import Action,Actor,execute_authorized
from .provenance import append_event_tx
from .runtime import database

class SubmissionError(ValueError):pass

def submit(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        invoice=connection.execute("select organization_id,contract_id,configuration_version_id,version,state from invoice_versions where id=%s",(invoice_id,)).fetchone()
    if not invoice:raise FileNotFoundError(invoice_id)
    scope=invoice_scope(actor,invoice_id)
    def command():
        att=current_attestation(actor,invoice_id)
        if invoice[4]!="draft":raise SubmissionError("Only a draft version may be submitted")
        if not att or not att["current"]:raise SubmissionError("A current attestation is required")
        with database() as connection:
            package=connection.execute("select id,zip_artifact_id from packages where invoice_version_id=%s and attestation_id=%s",(invoice_id,att["id"])).fetchone()
            if not package:raise SubmissionError("Generate the attested package before submission")
            hashes=connection.execute("select path,sha256 from package_artifacts where package_id=%s order by path",(package[0],)).fetchall()
            submission_id=f"submission-{uuid.uuid4().hex}";queue_id=f"queue-{uuid.uuid4().hex}"
            contract=connection.execute("select agency_organization_id,ngo_organization_id from contracts where id=%s",(invoice[1],)).fetchone()
            connection.execute("insert into submissions(id,invoice_version_id,package_id,actor_id,actor_role,configuration_version_id,invoice_version,package_hashes) values (%s,%s,%s,%s,%s,%s,%s,%s)",(submission_id,invoice_id,package[0],actor.user_id,actor.role.value,invoice[2],invoice[3],json.dumps(dict(hashes))))
            connection.execute("insert into government_queue_items(id,submission_id,agency_organization_id,ngo_organization_id) values (%s,%s,%s,%s)",(queue_id,submission_id,contract[0],contract[1]))
            connection.execute("update invoice_versions set state='submitted' where id=%s",(invoice_id,))
            connection.execute("update artifacts set submitted=true where id in (select artifact_id from package_artifacts where package_id=%s)",(package[0],))
            append_event_tx(connection,"submitted","invoice_version",invoice_id,actor_id=actor.user_id,organization_id=invoice[0],contract_id=invoice[1],payload={"submissionId":submission_id,"queueItemId":queue_id,"packageId":package[0],"invoiceVersion":invoice[3],"configurationVersionId":invoice[2],"packageHashes":dict(hashes)});connection.commit()
        return {"id":submission_id,"invoiceVersionId":invoice_id,"packageId":package[0],"queueItemId":queue_id,"invoiceVersion":invoice[3],"configurationVersionId":invoice[2],"packageHashes":dict(hashes),"state":"submitted"}
    return execute_authorized(actor,Action.SUBMIT,scope,command)
