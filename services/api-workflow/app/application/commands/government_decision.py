import json,uuid
from .access_scope import government_decision_scope
from ...authorization import Action,Actor,execute_authorized
from .provenance import append_event_tx
from .revision import create_return_revision_tx

from ..ports.statements import Statement
from ..transaction import transaction as database
REASONS={"EVIDENCE_CORRECTION","AMOUNT_CORRECTION","CLARIFICATION","APPROVED_AS_CORRECTED"}
class DecisionError(ValueError):pass

def decide(actor:Actor,queue_id:str,decision:str,reason_code:str,note:str,line_keys:list[str])->dict:
    with database() as connection:
        row=connection.read_models.execute(Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_QUEUE_ITEMS_INVOICE_VERSIONS_SUBMISSIONS_001,(queue_id,)).fetchone()
    if not row:raise FileNotFoundError(queue_id)
    scope=government_decision_scope(actor,queue_id)
    action=Action.RETURN if decision=="returned" else Action.APPROVE
    def command():
        if decision not in {"returned","approved"}:raise DecisionError("Unsupported decision")
        if reason_code not in REASONS or not note.strip():raise DecisionError("A supported reason and note are required")
        with database() as connection:
            human=connection.identity.execute(Statement.GOVERNMENT_DECISION_READ_USERS_002,(actor.user_id,)).fetchone()
            if human!=(actor.role.value,actor.organization_id):raise DecisionError("Decision actor must be a provisioned human reviewer")
            current=connection.workflow.execute(Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_QUEUE_ITEMS_003,(queue_id,)).fetchone()[0]
            if current!="submitted":raise DecisionError("Decision is stale or out of order")
            if decision=="returned" and connection.read_models.execute(Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_DECISIONS_INVOICE_VERSIONS_SUBMISSIONS_004,(row[7],)).fetchone():raise DecisionError("The canonical return has already occurred")
            if decision=="approved":
                prior=connection.read_models.execute(Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_DECISIONS_INVOICE_VERSIONS_SUBMISSIONS_005,(row[7],row[6])).fetchone()
                if row[6]<2 or not prior:raise DecisionError("Approval requires a corrected resubmission after return")
            decision_id=f"decision-{uuid.uuid4().hex}"
            connection.workflow.execute(Statement.GOVERNMENT_DECISION_WRITE_GOVERNMENT_DECISIONS_006,(decision_id,queue_id,row[3],row[4],row[5],decision,reason_code,note,json.dumps(line_keys),actor.user_id,actor.role.value))
            connection.workflow.execute(Statement.GOVERNMENT_DECISION_WRITE_GOVERNMENT_QUEUE_ITEMS_007,(decision,queue_id));connection.invoices.execute(Statement.GOVERNMENT_DECISION_WRITE_INVOICE_VERSIONS_008,(decision,row[4]))
            successor=None
            if decision=="returned":successor=create_return_revision_tx(connection,row[4],decision_id,actor.user_id,row[2],row[7])
            append_event_tx(connection,decision,"invoice_version",row[4],actor_id=actor.user_id,organization_id=row[1],contract_id=row[7],payload={"decisionId":decision_id,"queueItemId":queue_id,"submissionId":row[3],"packageId":row[5],"invoiceVersion":row[6],"reasonCode":reason_code,"note":note,"lineKeys":line_keys});connection.commit()
        return {"id":decision_id,"queueItemId":queue_id,"submissionId":row[3],"invoiceVersionId":row[4],"successorInvoiceVersionId":successor,"packageId":row[5],"invoiceVersion":row[6],"decision":decision,"reasonCode":reason_code,"note":note,"lineKeys":line_keys,"actorId":actor.user_id,"actorRole":actor.role.value}
    return execute_authorized(actor,action,scope,command)
