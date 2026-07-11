from decimal import Decimal
import uuid

from .authorization import Action, Actor, ResourceKind, ResourceScope, execute_authorized, require_permission
from .provenance import LineageInput, append_lineage_tx
from .runtime import database


class DraftAssemblyError(ValueError): pass


def _scope(resource_id: str, organization_id: str) -> ResourceScope:
    return ResourceScope(resource_id,ResourceKind.INVOICE,organization_id,ngo_organization_id=organization_id)


def assemble_draft(actor: Actor, contract_id: str) -> dict:
    def command():
        with database() as connection:
            ledger = connection.execute(
                "select id from ledger_imports where contract_id=%s and organization_id=%s order by created_at desc limit 1",
                (contract_id,actor.organization_id),
            ).fetchone()
            config = connection.execute(
                "select id,payload from configuration_versions where contract_id=%s order by version desc limit 1",(contract_id,)
            ).fetchone()
            if not ledger: raise DraftAssemblyError("Import a reconciled ledger before assembling the draft")
            if not config: raise DraftAssemblyError("Activate configuration before assembling the draft")
            existing = connection.execute(
                "select invoice_version_id from draft_assemblies where ledger_import_id=%s and configuration_version_id=%s",(ledger[0],config[0])
            ).fetchone()
            if existing: return get_draft(actor,existing[0])
            categories = {item["label"]:Decimal(str(item["limit"])) for item in config[1]["categories"]}
            expenses = connection.execute(
                """select id,expense_key,expense_date,vendor,description,budget_category,amount,evidence_filename,
                          source_artifact_id,source_sheet,source_cells->>'amount',mapping_version
                   from expense_rows where ledger_import_id=%s order by source_row""",(ledger[0],)
            ).fetchall()
            version = connection.execute("select coalesce(max(version),0)+1 from invoice_versions where contract_id=%s",(contract_id,)).fetchone()[0]
            invoice_id = f"invoice-{contract_id}-v{version}-{uuid.uuid4().hex[:8]}"
            total = sum((row[6] for row in expenses),Decimal("0.00"))
            connection.execute(
                """insert into invoice_versions(id,contract_id,version,configuration_version_id,state,organization_id,created_by,total)
                   values (%s,%s,%s,%s,'draft',%s,%s,%s)""",
                (invoice_id,contract_id,version,config[0],actor.organization_id,actor.user_id,total),
            )
            connection.execute("insert into draft_assemblies(invoice_version_id,ledger_import_id,configuration_version_id) values (%s,%s,%s)",(invoice_id,ledger[0],config[0]))
            for row in expenses:
                line_id=f"line-{uuid.uuid4().hex}"
                evidence=connection.execute(
                    """select id from artifacts where contract_id=%s and organization_id=%s and filename=%s
                       order by created_at desc limit 1""",(contract_id,actor.organization_id,row[7])
                ).fetchone()
                extraction_field=None; extraction_status="not_required"
                if evidence:
                    extraction=connection.execute(
                        """select f.id,f.proposed_value,f.reviewed_value,f.review_status
                           from extraction_fields f join extraction_runs r on r.id=f.extraction_run_id
                           where r.source_artifact_id=%s and f.field_name='amount' order by r.created_at desc limit 1""",(evidence[0],)
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
                connection.execute(
                    """insert into invoice_lines
                       (id,invoice_version_id,expense_row_id,expense_key,expense_date,vendor,description,budget_category,claimed_amount,
                        ledger_artifact_id,ledger_source_location,evidence_artifact_id,extraction_field_id,extraction_status,mapping_version)
                       values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (line_id,invoice_id,row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[8],source_location,
                     evidence[0] if evidence else None,extraction_field,extraction_status,row[11]),
                )
                predecessor=connection.execute(
                    "select id from field_lineage where field_name=%s and source_artifact_id=%s order by id desc limit 1",(f"{row[1]}.amount",row[8])
                ).fetchone()
                append_lineage_tx(connection,LineageInput(
                    contract_id,actor.organization_id,f"{row[1]}.claimedAmount",str(row[6]),row[8],source_location,
                    importer_version="ledger-importer-v1",mapping_version=row[11],invoice_version_id=invoice_id,
                    predecessor_lineage_id=predecessor[0] if predecessor else None,
                ))
            connection.commit()
        return get_draft(actor,invoice_id)
    return execute_authorized(actor,Action.CREATE,_scope(f"draft:{contract_id}",actor.organization_id),command)


def _finding(connection,invoice_id,expense_key,code,message):
    connection.execute("insert into invoice_findings(id,invoice_version_id,expense_key,code,message) values (%s,%s,%s,%s,%s)",(f"finding-{uuid.uuid4().hex}",invoice_id,expense_key,code,message))


def get_draft(actor: Actor, invoice_id: str) -> dict:
    with database() as connection:
        invoice=connection.execute(
            "select id,contract_id,version,configuration_version_id,state,organization_id,total from invoice_versions where id=%s",(invoice_id,)
        ).fetchone()
        if not invoice: raise FileNotFoundError(invoice_id)
        require_permission(actor,Action.READ,_scope(invoice_id,invoice[5]))
        lines=connection.execute(
            """select expense_key,expense_date,vendor,description,budget_category,claimed_amount,ledger_artifact_id,
                      ledger_source_location,evidence_artifact_id,extraction_status from invoice_lines where invoice_version_id=%s order by expense_key""",(invoice_id,)
        ).fetchall()
        config=connection.execute("select payload from configuration_versions where id=%s",(invoice[3],)).fetchone()[0]
        findings=connection.execute("select expense_key,code,message,status from invoice_findings where invoice_version_id=%s order by code,expense_key",(invoice_id,)).fetchall()
    category_totals={}
    for line in lines: category_totals[line[4]]=category_totals.get(line[4],Decimal("0.00"))+line[5]
    limits={item["label"]:Decimal(str(item["limit"])) for item in config["categories"]}
    categories=[{"name":name,"claimed":f"{category_totals.get(name,Decimal('0')):.2f}","limit":f"{limit:.2f}","available":f"{limit-category_totals.get(name,Decimal('0')):.2f}"} for name,limit in limits.items()]
    return {"id":invoice[0],"contractId":invoice[1],"version":invoice[2],"configurationVersionId":invoice[3],"state":invoice[4],"total":f"{invoice[6]:.2f}",
            "lines":[{"expenseKey":r[0],"date":r[1].isoformat(),"vendor":r[2],"description":r[3],"category":r[4],"amount":f"{r[5]:.2f}","ledgerArtifactId":r[6],"ledgerSource":r[7],"evidenceArtifactId":r[8],"extractionStatus":r[9]} for r in lines],
            "categories":categories,"findings":[{"expenseKey":r[0],"code":r[1],"message":r[2],"status":r[3]} for r in findings]}


def latest_draft(actor: Actor, contract_id: str) -> dict | None:
    with database() as connection:
        row=connection.execute("select id from invoice_versions where contract_id=%s and state='draft' order by version desc limit 1",(contract_id,)).fetchone()
    return get_draft(actor,row[0]) if row else None
