from datetime import date
import json
import uuid

from .access_scope import invoice_scope
from .authorization import Action,Actor,execute_authorized,require_permission
from .provenance import LineageInput,append_event,append_event_tx,append_lineage_tx
from .runtime import database
from .validation import execute_validation,latest_validation

class InvalidResolution(ValueError):pass

def current_findings(actor:Actor,invoice_id:str)->list[dict]:
    run=latest_validation(actor,invoice_id)
    if not run:return []
    with database() as connection:
        require_permission(actor,Action.READ,invoice_scope(actor,invoice_id))
        rows=connection.execute("""select f.id,f.expense_key,f.code,f.severity,f.message,f.status,r.normalized_input,l.evidence_artifact_id
                                   from validation_findings f join validation_results r on r.id=f.validation_result_id
                                   left join invoice_lines l on l.invoice_version_id=f.invoice_version_id and l.expense_key=f.expense_key
                                   where f.validation_run_id=%s order by f.severity,f.code""",(run["id"],)).fetchall()
    return [{"id":r[0],"expenseKey":r[1],"code":r[2],"severity":r[3],"message":r[4],"status":r[5],"normalizedInput":r[6],"evidenceArtifactId":r[7],"remediation":_remediation(r[2],r[3])} for r in rows]

def _remediation(code,severity):
    if code.startswith("SERVICE_PERIOD:"):return "Correct the service date to the configured period and revalidate."
    if severity=="warning":return "Explain or dismiss the warning, then retain the new validation run."
    if code.startswith("REQUIRED_EVIDENCE:"):return "Upload or replace the required evidence and revalidate."
    return "Correct the affected invoice input and revalidate."

def has_open_blockers(invoice_id:str)->bool:
    with database() as connection:
        run=connection.execute("select id from validation_runs where invoice_version_id=%s and engine_version is not null order by created_at desc,id desc limit 1",(invoice_id,)).fetchone()
        if not run:return True
        return connection.execute("select exists(select 1 from validation_findings where validation_run_id=%s and severity='blocker' and status='open')",(run[0],)).fetchone()[0]

def resolve_finding(actor:Actor,finding_id:str,action:str,reason:str,correction_value:str|None=None)->dict:
    if action not in {"correct","explain","dismiss"} or not reason.strip():raise InvalidResolution("Resolution action and reason are required")
    with database() as connection:
        finding=connection.execute("""select f.invoice_version_id,f.expense_key,f.code,f.severity,f.status,i.organization_id
                                      from validation_findings f join invoice_versions i on i.id=f.invoice_version_id where f.id=%s""",(finding_id,)).fetchone()
    if not finding:raise FileNotFoundError(finding_id)
    def command():
        if finding[4]!="open":raise InvalidResolution("Finding is not open")
        if finding[3]=="blocker":
            if action!="correct":raise InvalidResolution("Blockers require correction")
            if not finding[2].startswith("SERVICE_PERIOD:") or not correction_value:raise InvalidResolution("This blocker requires a supported correction value")
            try:corrected=date.fromisoformat(correction_value)
            except ValueError as error:raise InvalidResolution("Correction must be an ISO date") from error
            with database() as connection:
                line=connection.execute("select id,expense_date,ledger_artifact_id,ledger_source_location from invoice_lines where invoice_version_id=%s and expense_key=%s for update",(finding[0],finding[1])).fetchone()
                correction_id=f"line-correction-{uuid.uuid4().hex}"
                predecessor=connection.execute("select id from field_lineage where invoice_version_id=%s and field_name=%s order by id desc limit 1",(finding[0],f"{finding[1]}.claimedAmount")).fetchone()
                lineage=append_lineage_tx(connection,LineageInput(
                    connection.execute("select contract_id from invoice_versions where id=%s",(finding[0],)).fetchone()[0],finding[5],f"{finding[1]}.expenseDate",corrected.isoformat(),line[2],line[3],
                    correction_actor_id=actor.user_id,correction_reason=reason,invoice_version_id=finding[0],predecessor_lineage_id=predecessor[0] if predecessor else None,
                ))
                connection.execute("insert into invoice_line_corrections(id,invoice_version_id,invoice_line_id,field_name,prior_value,corrected_value,actor_id,reason) values (%s,%s,%s,'expense_date',%s,%s,%s,%s)",(correction_id,finding[0],line[0],line[1].isoformat(),corrected.isoformat(),actor.user_id,reason))
                connection.execute("update invoice_lines set expense_date=%s where id=%s",(corrected,line[0]))
                connection.execute("update invoice_versions set material_revision=material_revision+1 where id=%s",(finding[0],))
                append_event_tx(connection,"invoice_line_corrected","invoice_line",line[0],actor_id=actor.user_id,organization_id=finding[5],contract_id=connection.execute("select contract_id from invoice_versions where id=%s",(finding[0],)).fetchone()[0],payload={"expenseKey":finding[1],"field":"expense_date","priorValue":line[1].isoformat(),"correctedValue":corrected.isoformat(),"correctionId":correction_id,"lineageId":lineage})
                connection.commit()
        elif finding[3]!="warning" or action not in {"explain","dismiss"}:raise InvalidResolution("Warnings may be explained or dismissed")
        new_run=execute_validation(actor,finding[0])
        with database() as connection:
            if finding[3]=="warning":connection.execute("update validation_findings set status='dismissed' where validation_run_id=%s and code=%s",(new_run["id"],finding[2]))
            connection.execute("update validation_findings set status=%s where id=%s",("resolved" if action=="correct" else "dismissed",finding_id))
            resolution_id=f"finding-resolution-{uuid.uuid4().hex}"
            connection.execute("insert into finding_resolutions(id,prior_finding_id,invoice_version_id,action,actor_id,reason,new_validation_run_id) values (%s,%s,%s,%s,%s,%s,%s)",(resolution_id,finding_id,finding[0],action,actor.user_id,reason,new_run["id"]))
            append_event_tx(connection,"finding_resolved","validation_finding",finding_id,actor_id=actor.user_id,organization_id=finding[5],contract_id=connection.execute("select contract_id from invoice_versions where id=%s",(finding[0],)).fetchone()[0],payload={"action":action,"reason":reason,"newValidationRunId":new_run["id"],"resolutionId":resolution_id})
            connection.commit()
        return {"id":resolution_id,"priorFindingId":finding_id,"action":action,"reason":reason,"newValidationRunId":new_run["id"],"findings":current_findings(actor,finding[0]),"hasOpenBlockers":has_open_blockers(finding[0])}
    return execute_authorized(actor,Action.UPDATE,invoice_scope(actor,finding[0]),command)
