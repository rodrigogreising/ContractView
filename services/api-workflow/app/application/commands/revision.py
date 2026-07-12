import uuid
from .access_scope import invoice_scope
from ...authorization import Action,Actor,execute_authorized
from .provenance import append_event_tx

from ..ports.statements import Statement
from ..transaction import transaction as database
class RevisionError(ValueError):pass

def create_return_revision_tx(connection,invoice_id:str,decision_id:str,actor_id:str,organization_id:str,contract_id:str)->str:
    existing=connection.invoices.execute(Statement.REVISION_READ_INVOICE_VERSION_LINKS_001,(invoice_id,)).fetchone()
    if existing:return existing[0]
    source=connection.invoices.execute(Statement.REVISION_READ_INVOICE_VERSIONS_002,(invoice_id,)).fetchone()
    successor=f"invoice-{uuid.uuid4().hex}";version=source[0]+1
    connection.invoices.execute(Statement.REVISION_WRITE_INVOICE_VERSIONS_003,(successor,contract_id,version,source[1],source[2],actor_id,source[3]))
    connection.invoices.execute(Statement.REVISION_WRITE_INVOICE_LINES_004,(successor,invoice_id))
    connection.invoices.execute(Statement.REVISION_WRITE_INVOICE_VERSION_LINKS_005,(invoice_id,successor,decision_id))
    append_event_tx(connection,"revision_created","invoice_version",successor,actor_id=actor_id,organization_id=organization_id,contract_id=contract_id,payload={"predecessorInvoiceVersionId":invoice_id,"governmentDecisionId":decision_id,"version":version})
    return successor

def revision_feedback(actor:Actor,contract_id:str)->dict|None:
    with database() as connection:
        row=connection.read_models.execute(Statement.REVISION_READ_GOVERNMENT_DECISIONS_INVOICE_VERSION_LINKS_INVOICE_VERSIONS_006,(contract_id,)).fetchone()
        if not row:return None
        org=connection.invoices.execute(Statement.REVISION_READ_INVOICE_VERSIONS_007,(row[0],)).fetchone()[0]
    scope=invoice_scope(actor,row[0])
    def command():return {"invoiceVersionId":row[0],"predecessorInvoiceVersionId":row[1],"decisionId":row[2],"reasonCode":row[3],"note":row[4],"lineKeys":row[5]}
    return execute_authorized(actor,Action.READ,scope,command)

def correct_revision(actor:Actor,invoice_id:str,expense_key:str,description:str,reason:str)->dict:
    with database() as connection:
        invoice=connection.invoices.execute(Statement.REVISION_READ_INVOICE_VERSIONS_008,(invoice_id,)).fetchone()
    if not invoice:raise FileNotFoundError(invoice_id)
    scope=invoice_scope(actor,invoice_id)
    def command():
        if invoice[2]!="draft" or not description.strip() or not reason.strip():raise RevisionError("An editable revision, corrected description, and reason are required")
        with database() as connection:
            prior=connection.invoices.execute(Statement.REVISION_READ_INVOICE_LINES_009,(invoice_id,expense_key)).fetchone()
            if not prior:raise RevisionError("Feedback line was not found")
            correction_id=f"revision-correction-{uuid.uuid4().hex}"
            connection.invoices.execute(Statement.REVISION_WRITE_INVOICE_LINES_010,(description,invoice_id,expense_key));connection.invoices.execute(Statement.REVISION_WRITE_INVOICE_VERSIONS_011,(invoice_id,))
            connection.invoices.execute(Statement.REVISION_WRITE_REVISION_CORRECTIONS_012,(correction_id,invoice_id,expense_key,prior[0],description,reason,actor.user_id))
            append_event_tx(connection,"invoice_line_corrected","invoice_version",invoice_id,actor_id=actor.user_id,organization_id=invoice[0],contract_id=invoice[1],payload={"correctionId":correction_id,"expenseKey":expense_key,"field":"description","priorValue":prior[0],"correctedValue":description,"reason":reason});connection.commit()
        return {"id":correction_id,"invoiceVersionId":invoice_id,"expenseKey":expense_key,"priorValue":prior[0],"correctedValue":description,"reason":reason}
    return execute_authorized(actor,Action.UPDATE,scope,command)
