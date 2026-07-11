import uuid
from .authorization import Action,Actor,ResourceKind,ResourceScope,execute_authorized
from .provenance import append_event_tx
from .runtime import database

class RevisionError(ValueError):pass

def create_return_revision_tx(connection,invoice_id:str,decision_id:str,actor_id:str,organization_id:str,contract_id:str)->str:
    existing=connection.execute("select successor_invoice_version_id from invoice_version_links where predecessor_invoice_version_id=%s",(invoice_id,)).fetchone()
    if existing:return existing[0]
    source=connection.execute("select version,configuration_version_id,organization_id,total from invoice_versions where id=%s",(invoice_id,)).fetchone()
    successor=f"invoice-{uuid.uuid4().hex}";version=source[0]+1
    connection.execute("insert into invoice_versions(id,contract_id,version,configuration_version_id,state,organization_id,created_by,total,material_revision) values (%s,%s,%s,%s,'draft',%s,%s,%s,1)",(successor,contract_id,version,source[1],source[2],actor_id,source[3]))
    connection.execute("""insert into invoice_lines(id,invoice_version_id,expense_row_id,expense_key,expense_date,vendor,description,budget_category,claimed_amount,ledger_artifact_id,ledger_source_location,evidence_artifact_id,extraction_field_id,extraction_status,mapping_version)
      select 'line-'||md5(random()::text||id),%s,expense_row_id,expense_key,expense_date,vendor,description,budget_category,claimed_amount,ledger_artifact_id,ledger_source_location,evidence_artifact_id,extraction_field_id,extraction_status,mapping_version from invoice_lines where invoice_version_id=%s""",(successor,invoice_id))
    connection.execute("insert into invoice_version_links values (%s,%s,'corrects_return',%s,now())",(invoice_id,successor,decision_id))
    append_event_tx(connection,"revision_created","invoice_version",successor,actor_id=actor_id,organization_id=organization_id,contract_id=contract_id,payload={"predecessorInvoiceVersionId":invoice_id,"governmentDecisionId":decision_id,"version":version})
    return successor

def revision_feedback(actor:Actor,contract_id:str)->dict|None:
    with database() as connection:
        row=connection.execute("""select l.successor_invoice_version_id,l.predecessor_invoice_version_id,d.id,d.reason_code,d.note,d.line_keys
          from invoice_version_links l join government_decisions d on d.id=l.government_decision_id join invoice_versions i on i.id=l.successor_invoice_version_id where i.contract_id=%s and i.state='draft' order by i.version desc limit 1""",(contract_id,)).fetchone()
        if not row:return None
        org=connection.execute("select organization_id from invoice_versions where id=%s",(row[0],)).fetchone()[0]
    scope=ResourceScope(row[0],ResourceKind.INVOICE,org,ngo_organization_id=org)
    def command():return {"invoiceVersionId":row[0],"predecessorInvoiceVersionId":row[1],"decisionId":row[2],"reasonCode":row[3],"note":row[4],"lineKeys":row[5]}
    return execute_authorized(actor,Action.READ,scope,command)

def correct_revision(actor:Actor,invoice_id:str,expense_key:str,description:str,reason:str)->dict:
    with database() as connection:
        invoice=connection.execute("select organization_id,contract_id,state from invoice_versions where id=%s",(invoice_id,)).fetchone()
    if not invoice:raise FileNotFoundError(invoice_id)
    scope=ResourceScope(invoice_id,ResourceKind.INVOICE,invoice[0],ngo_organization_id=invoice[0])
    def command():
        if invoice[2]!="draft" or not description.strip() or not reason.strip():raise RevisionError("An editable revision, corrected description, and reason are required")
        with database() as connection:
            prior=connection.execute("select description from invoice_lines where invoice_version_id=%s and expense_key=%s",(invoice_id,expense_key)).fetchone()
            if not prior:raise RevisionError("Feedback line was not found")
            correction_id=f"revision-correction-{uuid.uuid4().hex}"
            connection.execute("update invoice_lines set description=%s where invoice_version_id=%s and expense_key=%s",(description,invoice_id,expense_key));connection.execute("update invoice_versions set material_revision=material_revision+1 where id=%s",(invoice_id,))
            connection.execute("insert into revision_corrections values (%s,%s,%s,'description',%s,%s,%s,%s,now())",(correction_id,invoice_id,expense_key,prior[0],description,reason,actor.user_id))
            append_event_tx(connection,"invoice_line_corrected","invoice_version",invoice_id,actor_id=actor.user_id,organization_id=invoice[0],contract_id=invoice[1],payload={"correctionId":correction_id,"expenseKey":expense_key,"field":"description","priorValue":prior[0],"correctedValue":description,"reason":reason});connection.commit()
        return {"id":correction_id,"invoiceVersionId":invoice_id,"expenseKey":expense_key,"priorValue":prior[0],"correctedValue":description,"reason":reason}
    return execute_authorized(actor,Action.UPDATE,scope,command)
