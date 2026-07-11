from decimal import Decimal

from .authorization import Action,Actor,ResourceKind,ResourceScope,require_permission
from .runtime import database

def calculate_budget(category_amounts:dict[str,Decimal],categories:list[dict])->dict:
    rows=[]
    for category in categories:
        budgeted=Decimal(str(category["limit"])).quantize(Decimal("0.01"));requested=category_amounts.get(category["label"],Decimal("0.00")).quantize(Decimal("0.01"));remaining=budgeted-requested
        rows.append({"code":category["code"],"name":category["label"],"requested":requested,"budgeted":budgeted,"remaining":remaining,"overBudget":remaining<0})
    requested_total=sum((row["requested"] for row in rows),Decimal("0.00"));budgeted_total=sum((row["budgeted"] for row in rows),Decimal("0.00"));remaining_total=budgeted_total-requested_total
    return {"categories":rows,"total":{"requested":requested_total,"budgeted":budgeted_total,"remaining":remaining_total,"overBudget":any(row["overBudget"] for row in rows)}}

def budget_snapshot(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        invoice=connection.execute("""select i.configuration_version_id,i.organization_id,i.state,c.agency_organization_id,c.ngo_organization_id
                                      from invoice_versions i join contracts c on c.id=i.contract_id where i.id=%s""",(invoice_id,)).fetchone()
        if not invoice:raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,ResourceScope(invoice_id,ResourceKind.INVOICE,invoice[1],agency_organization_id=invoice[3],ngo_organization_id=invoice[4],submitted=invoice[2] != "draft"))
        config=connection.execute("select version,payload from configuration_versions where id=%s",(invoice[0],)).fetchone()
        amounts=dict(connection.execute("select budget_category,sum(claimed_amount) from invoice_lines where invoice_version_id=%s group by budget_category",(invoice_id,)).fetchall())
    calculated=calculate_budget(amounts,config[1]["categories"])
    def encode(row):return {**row,"requested":f"{row['requested']:.2f}","budgeted":f"{row['budgeted']:.2f}","remaining":f"{row['remaining']:.2f}"}
    return {"invoiceVersionId":invoice_id,"configurationVersionId":invoice[0],"configurationVersion":config[0],"categories":[encode(row) for row in calculated["categories"]],"total":encode(calculated["total"])}
