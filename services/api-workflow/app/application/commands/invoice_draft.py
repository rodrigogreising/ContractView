from decimal import Decimal
import uuid

from .access_scope import contract_scope, invoice_scope
from ...authorization import Action, Actor, ResourceKind, execute_authorized, require_permission
from .provenance import LineageInput, append_lineage_tx, append_relation_tx


from ..ports.statements import Statement
from ..transaction import transaction as database
class DraftAssemblyError(ValueError): pass


def assemble_draft(actor: Actor, contract_id: str) -> dict:
    def command():
        with database() as connection:
            ledger = connection.extraction.execute(Statement.INVOICE_DRAFT_READ_LEDGER_IMPORTS_001,
                (contract_id,actor.organization_id),
            ).fetchone()
            config = connection.configuration.execute(Statement.INVOICE_DRAFT_READ_CONFIGURATION_VERSIONS_002,(contract_id,)
            ).fetchone()
            if not ledger: raise DraftAssemblyError("Import a reconciled ledger before assembling the draft")
            if not config: raise DraftAssemblyError("Activate configuration before assembling the draft")
            existing = connection.invoices.execute(Statement.INVOICE_DRAFT_READ_DRAFT_ASSEMBLIES_003,(ledger[0],config[0])
            ).fetchone()
            if existing: return get_draft(actor,existing[0])
            categories = {item["label"]:Decimal(str(item["limit"])) for item in config[1]["categories"]}
            expenses = connection.extraction.execute(Statement.INVOICE_DRAFT_READ_EXPENSE_ROWS_004,(ledger[0],)
            ).fetchall()
            version = connection.invoices.execute(Statement.INVOICE_DRAFT_READ_INVOICE_VERSIONS_005,(contract_id,)).fetchone()[0]
            invoice_id = f"invoice-{contract_id}-v{version}-{uuid.uuid4().hex[:8]}"
            total = sum((row[6] for row in expenses),Decimal("0.00"))
            connection.invoices.execute(Statement.INVOICE_DRAFT_WRITE_INVOICE_VERSIONS_006,
                (invoice_id,contract_id,version,config[0],actor.organization_id,actor.user_id,total),
            )
            connection.invoices.execute(Statement.INVOICE_DRAFT_WRITE_DRAFT_ASSEMBLIES_007,(invoice_id,ledger[0],config[0]))
            for row in expenses:
                line_id=f"line-{uuid.uuid4().hex}"
                evidence=connection.artifacts.execute(Statement.INVOICE_DRAFT_READ_ARTIFACTS_008,(contract_id,actor.organization_id,row[7])
                ).fetchone()
                extraction_field=None; extraction_status="not_required"
                if evidence:
                    extraction=connection.extraction.execute(Statement.INVOICE_DRAFT_READ_EXTRACTION_FIELDS_EXTRACTION_RUNS_009,(evidence[0],)
                    ).fetchone()
                    if extraction:
                        extraction_field=extraction[0]; extraction_status=extraction[3]
                        if extraction[3] == "proposed":
                            _finding(connection,invoice_id,row[1],"UNREVIEWED_EXTRACTION","Review the proposed evidence amount before validation")
                        elif Decimal(extraction[2]) != row[6]:
                            _finding(connection,invoice_id,row[1],"EVIDENCE_AMOUNT_MISMATCH",f"Reviewed evidence amount {extraction[2]} does not match ledger amount {row[6]}")
                else:
                    extraction_status="missing"
                    _finding(connection,invoice_id,row[1],"MISSING_EVIDENCE",f"Upload supporting evidence {row[7]}")
                if row[5] not in categories:
                    _finding(connection,invoice_id,row[1],"UNMAPPED_CATEGORY",f"Category {row[5]} is not configured")
                source_location=f"{row[9]}!{row[10]}"
                connection.invoices.execute(Statement.INVOICE_DRAFT_WRITE_INVOICE_LINES_010,
                    (line_id,invoice_id,row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[8],source_location,
                     evidence[0] if evidence else None,extraction_field,extraction_status,row[13]),
                )
                invoice_ref={"kind":"invoice","id":invoice_id,"version":version}
                append_relation_tx(connection,contract_id,actor.organization_id,"maps_to",
                    {"kind":"entity","id":row[0],"version":row[13]},invoice_ref,actor=actor)
                append_relation_tx(connection,contract_id,actor.organization_id,"supports",
                    {"kind":"artifact","id":row[8],"version":1},invoice_ref,actor=actor)
                if evidence:
                    append_relation_tx(connection,contract_id,actor.organization_id,"supports",
                        {"kind":"artifact","id":evidence[0],"version":1},invoice_ref,actor=actor)
                mapped_fields = (
                    ("claimedAmount", "amount", str(row[6]), row[10]),
                    ("expenseDate", "expense_date", row[2].isoformat(), row[11]),
                    ("description", "description", row[4], row[12]),
                )
                for invoice_field, source_field, value, cell in mapped_fields:
                    predecessor=connection.provenance.execute(Statement.INVOICE_DRAFT_READ_FIELD_LINEAGE_011,(f"{row[1]}.{source_field}",row[8])
                    ).fetchone()
                    append_lineage_tx(connection,LineageInput(
                        contract_id,actor.organization_id,f"{row[1]}.{invoice_field}",value,row[8],f"{row[9]}!{cell}",
                        importer_version="ledger-importer-v1",mapping_version=row[13],invoice_version_id=invoice_id,
                        predecessor_lineage_id=predecessor[0] if predecessor else None,
                    ))
            connection.commit()
        return get_draft(actor,invoice_id)
    scope = contract_scope(actor, contract_id, f"draft:{contract_id}", ResourceKind.INVOICE)
    return execute_authorized(actor,Action.CREATE,scope,command)


def _finding(connection,invoice_id,expense_key,code,message):
    connection.invoices.execute(Statement.INVOICE_DRAFT_WRITE_INVOICE_FINDINGS_012,(f"finding-{uuid.uuid4().hex}",invoice_id,expense_key,code,message))


def get_draft(actor: Actor, invoice_id: str) -> dict:
    with database() as connection:
        invoice=connection.invoices.execute(Statement.INVOICE_DRAFT_READ_INVOICE_VERSIONS_013,(invoice_id,)
        ).fetchone()
        if not invoice: raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,invoice_scope(actor,invoice_id))
        lines=connection.invoices.execute(Statement.INVOICE_DRAFT_READ_INVOICE_LINES_014,(invoice_id,)
        ).fetchall()
        config=connection.configuration.execute(Statement.INVOICE_DRAFT_READ_CONFIGURATION_VERSIONS_015,(invoice[3],)).fetchone()[0]
        findings=connection.invoices.execute(Statement.INVOICE_DRAFT_READ_INVOICE_FINDINGS_016,(invoice_id,)).fetchall()
    category_totals={}
    for line in lines: category_totals[line[4]]=category_totals.get(line[4],Decimal("0.00"))+line[5]
    limits={item["label"]:Decimal(str(item["limit"])) for item in config["categories"]}
    categories=[{"name":name,"claimed":f"{category_totals.get(name,Decimal('0')):.2f}","limit":f"{limit:.2f}","available":f"{limit-category_totals.get(name,Decimal('0')):.2f}"} for name,limit in limits.items()]
    return {"id":invoice[0],"contractId":invoice[1],"version":invoice[2],"configurationVersionId":invoice[3],"state":invoice[4],"total":f"{invoice[6]:.2f}",
            "lines":[{"expenseKey":r[0],"date":r[1].isoformat(),"vendor":r[2],"description":r[3],"category":r[4],"amount":f"{r[5]:.2f}","ledgerArtifactId":r[6],"ledgerSource":r[7],"evidenceArtifactId":r[8],"extractionStatus":r[9]} for r in lines],
            "categories":categories,"findings":[{"expenseKey":r[0],"code":r[1],"message":r[2],"status":r[3]} for r in findings]}


def latest_draft(actor: Actor, contract_id: str) -> dict | None:
    require_permission(
        actor,
        Action.READ,
        contract_scope(actor, contract_id, f"draft:{contract_id}", ResourceKind.INVOICE),
    )
    with database() as connection:
        row=connection.invoices.execute(Statement.INVOICE_DRAFT_READ_INVOICE_VERSIONS_017,(contract_id,)).fetchone()
    return get_draft(actor,row[0]) if row else None
