import json,uuid
from .authorization import Action,Actor,ResourceKind,ResourceScope,execute_authorized
from .provenance import append_event_tx
from .runtime import database
from .revision import create_return_revision_tx

REASONS={"EVIDENCE_CORRECTION","AMOUNT_CORRECTION","CLARIFICATION","APPROVED_AS_CORRECTED"}
class DecisionError(ValueError):pass

def decide(actor:Actor,queue_id:str,decision:str,reason_code:str,note:str,line_keys:list[str])->dict:
    with database() as connection:
        row=connection.execute("""select q.status,q.agency_organization_id,q.ngo_organization_id,s.id,s.invoice_version_id,s.package_id,iv.version,iv.contract_id
          from government_queue_items q join submissions s on s.id=q.submission_id join invoice_versions iv on iv.id=s.invoice_version_id where q.id=%s""",(queue_id,)).fetchone()
    if not row:raise FileNotFoundError(queue_id)
    scope=ResourceScope(queue_id,ResourceKind.GOVERNMENT_DECISION,row[1],agency_organization_id=row[1],ngo_organization_id=row[2],submitted=True)
    action=Action.RETURN if decision=="returned" else Action.APPROVE
    def command():
        if decision not in {"returned","approved"}:raise DecisionError("Unsupported decision")
        if reason_code not in REASONS or not note.strip():raise DecisionError("A supported reason and note are required")
        with database() as connection:
            human=connection.execute("select role,organization_id from users where id=%s",(actor.user_id,)).fetchone()
            if human!=(actor.role.value,actor.organization_id):raise DecisionError("Decision actor must be a provisioned human reviewer")
            current=connection.execute("select status from government_queue_items where id=%s for update",(queue_id,)).fetchone()[0]
            if current!="submitted":raise DecisionError("Decision is stale or out of order")
            if decision=="returned" and connection.execute("select 1 from government_decisions d join submissions s on s.id=d.submission_id join invoice_versions i on i.id=s.invoice_version_id where i.contract_id=%s and d.decision='returned'",(row[7],)).fetchone():raise DecisionError("The canonical return has already occurred")
            if decision=="approved":
                prior=connection.execute("""select 1 from government_decisions d join submissions s on s.id=d.submission_id join invoice_versions i on i.id=s.invoice_version_id
                    where i.contract_id=%s and d.decision='returned' and i.version < %s""",(row[7],row[6])).fetchone()
                if row[6]<2 or not prior:raise DecisionError("Approval requires a corrected resubmission after return")
            decision_id=f"decision-{uuid.uuid4().hex}"
            connection.execute("insert into government_decisions(id,queue_item_id,submission_id,invoice_version_id,package_id,decision,reason_code,note,line_keys,actor_id,actor_role) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(decision_id,queue_id,row[3],row[4],row[5],decision,reason_code,note,json.dumps(line_keys),actor.user_id,actor.role.value))
            connection.execute("update government_queue_items set status=%s where id=%s",(decision,queue_id));connection.execute("update invoice_versions set state=%s where id=%s",(decision,row[4]))
            successor=None
            if decision=="returned":successor=create_return_revision_tx(connection,row[4],decision_id,actor.user_id,row[2],row[7])
            append_event_tx(connection,decision,"invoice_version",row[4],actor_id=actor.user_id,organization_id=row[1],contract_id=row[7],payload={"decisionId":decision_id,"queueItemId":queue_id,"submissionId":row[3],"packageId":row[5],"invoiceVersion":row[6],"reasonCode":reason_code,"note":note,"lineKeys":line_keys});connection.commit()
        return {"id":decision_id,"queueItemId":queue_id,"submissionId":row[3],"invoiceVersionId":row[4],"successorInvoiceVersionId":successor,"packageId":row[5],"invoiceVersion":row[6],"decision":decision,"reasonCode":reason_code,"note":note,"lineKeys":line_keys,"actorId":actor.user_id,"actorRole":actor.role.value}
    return execute_authorized(actor,action,scope,command)
