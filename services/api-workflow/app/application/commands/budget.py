from decimal import Decimal

from .access_scope import invoice_scope
from ...authorization import Action,Actor,require_permission

from ..ports.statements import Statement
from ..transaction import transaction as database
def calculate_budget(category_amounts:dict[str,Decimal],categories:list[dict])->dict:
    rows=[]
    for category in categories:
        budgeted=Decimal(str(category["limit"])).quantize(Decimal("0.01"));requested=category_amounts.get(category["label"],Decimal("0.00")).quantize(Decimal("0.01"));remaining=budgeted-requested
        rows.append({"code":category["code"],"name":category["label"],"requested":requested,"budgeted":budgeted,"remaining":remaining,"overBudget":remaining<0})
    requested_total=sum((row["requested"] for row in rows),Decimal("0.00"));budgeted_total=sum((row["budgeted"] for row in rows),Decimal("0.00"));remaining_total=budgeted_total-requested_total
    return {"categories":rows,"total":{"requested":requested_total,"budgeted":budgeted_total,"remaining":remaining_total,"overBudget":any(row["overBudget"] for row in rows)}}

def budget_snapshot(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        invoice=connection.read_models.execute(Statement.BUDGET_READ_CONTRACTS_INVOICE_VERSIONS_001,(invoice_id,)).fetchone()
        if not invoice:raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,invoice_scope(actor,invoice_id))
        config=connection.configuration.execute(Statement.BUDGET_READ_CONFIGURATION_VERSIONS_002,(invoice[0],)).fetchone()
        amounts=dict(connection.invoices.execute(Statement.BUDGET_READ_INVOICE_LINES_003,(invoice_id,)).fetchall())
    calculated=calculate_budget(amounts,config[1]["categories"])
    def encode(row):return {**row,"requested":f"{row['requested']:.2f}","budgeted":f"{row['budgeted']:.2f}","remaining":f"{row['remaining']:.2f}"}
    return {"invoiceVersionId":invoice_id,"configurationVersionId":invoice[0],"configurationVersion":config[0],"categories":[encode(row) for row in calculated["categories"]],"total":encode(calculated["total"])}
