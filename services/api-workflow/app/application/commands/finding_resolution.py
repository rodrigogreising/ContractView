from datetime import date
import json
import uuid

from .access_scope import invoice_scope
from ...authorization import Action,Actor,execute_authorized,require_permission
from .provenance import LineageInput,append_event,append_event_tx,append_lineage_tx
from .validation import execute_validation,latest_validation

from ..ports.statements import Statement
from ..transaction import transaction as database
class InvalidResolution(ValueError):pass

def current_findings(actor:Actor,invoice_id:str)->list[dict]:
    run=latest_validation(actor,invoice_id)
    if not run:return []
    with database() as connection:
        require_permission(actor,Action.READ,invoice_scope(actor,invoice_id))
        rows=connection.read_models.execute(Statement.FINDING_RESOLUTION_READ_INVOICE_LINES_VALIDATION_FINDINGS_VALIDATION_RESULTS_001,(run["id"],)).fetchall()
    return [{"id":r[0],"expenseKey":r[1],"code":r[2],"severity":r[3],"message":r[4],"status":r[5],"normalizedInput":r[6],"evidenceArtifactId":r[7],"remediation":_remediation(r[2],r[3])} for r in rows]

def _remediation(code,severity):
    if code.startswith("SERVICE_PERIOD:"):return "Correct the service date to the configured period and revalidate."
    if severity=="warning":return "Explain or dismiss the warning, then retain the new validation run."
    if code.startswith("REQUIRED_EVIDENCE:"):return "Upload or replace the required evidence and revalidate."
    return "Correct the affected invoice input and revalidate."

def has_open_blockers(invoice_id:str)->bool:
    with database() as connection:
        run=connection.validation.execute(Statement.FINDING_RESOLUTION_READ_VALIDATION_RUNS_002,(invoice_id,)).fetchone()
        if not run:return True
        return connection.validation.execute(Statement.FINDING_RESOLUTION_READ_VALIDATION_FINDINGS_003,(run[0],)).fetchone()[0]

def resolve_finding(actor:Actor,finding_id:str,action:str,reason:str,correction_value:str|None=None)->dict:
    if action not in {"correct","explain","dismiss"} or not reason.strip():raise InvalidResolution("Resolution action and reason are required")
    with database() as connection:
        finding=connection.read_models.execute(Statement.FINDING_RESOLUTION_READ_INVOICE_VERSIONS_VALIDATION_FINDINGS_004,(finding_id,)).fetchone()
    if not finding:raise FileNotFoundError(finding_id)
    def command():
        if finding[4]!="open":raise InvalidResolution("Finding is not open")
        if finding[3]=="blocker":
            if action!="correct":raise InvalidResolution("Blockers require correction")
            if not finding[2].startswith("SERVICE_PERIOD:") or not correction_value:raise InvalidResolution("This blocker requires a supported correction value")
            try:corrected=date.fromisoformat(correction_value)
            except ValueError as error:raise InvalidResolution("Correction must be an ISO date") from error
            with database() as connection:
                line=connection.invoices.execute(Statement.FINDING_RESOLUTION_READ_INVOICE_LINES_005,(finding[0],finding[1])).fetchone()
                correction_id=f"line-correction-{uuid.uuid4().hex}"
                predecessor=connection.provenance.execute(Statement.FINDING_RESOLUTION_READ_FIELD_LINEAGE_006,(finding[0],f"{finding[1]}.claimedAmount")).fetchone()
                lineage=append_lineage_tx(connection,LineageInput(
                    connection.invoices.execute(Statement.FINDING_RESOLUTION_READ_INVOICE_VERSIONS_007,(finding[0],)).fetchone()[0],finding[5],f"{finding[1]}.expenseDate",corrected.isoformat(),line[2],line[3],
                    correction_actor_id=actor.user_id,correction_reason=reason,invoice_version_id=finding[0],predecessor_lineage_id=predecessor[0] if predecessor else None,
                ))
                connection.invoices.execute(Statement.FINDING_RESOLUTION_WRITE_INVOICE_LINE_CORRECTIONS_008,(correction_id,finding[0],line[0],line[1].isoformat(),corrected.isoformat(),actor.user_id,reason))
                connection.invoices.execute(Statement.FINDING_RESOLUTION_WRITE_INVOICE_LINES_009,(corrected,line[0]))
                connection.invoices.execute(Statement.FINDING_RESOLUTION_WRITE_INVOICE_VERSIONS_010,(finding[0],))
                append_event_tx(connection,"invoice_line_corrected","invoice_line",line[0],actor_id=actor.user_id,organization_id=finding[5],contract_id=connection.invoices.execute(Statement.FINDING_RESOLUTION_READ_INVOICE_VERSIONS_007,(finding[0],)).fetchone()[0],payload={"expenseKey":finding[1],"field":"expense_date","priorValue":line[1].isoformat(),"correctedValue":corrected.isoformat(),"correctionId":correction_id,"lineageId":lineage})
                connection.commit()
        elif finding[3]!="warning" or action not in {"explain","dismiss"}:raise InvalidResolution("Warnings may be explained or dismissed")
        new_run=execute_validation(actor,finding[0])
        with database() as connection:
            if finding[3]=="warning":connection.validation.execute(Statement.FINDING_RESOLUTION_WRITE_VALIDATION_FINDINGS_012,(new_run["id"],finding[2]))
            connection.validation.execute(Statement.FINDING_RESOLUTION_WRITE_VALIDATION_FINDINGS_013,("resolved" if action=="correct" else "dismissed",finding_id))
            resolution_id=f"finding-resolution-{uuid.uuid4().hex}"
            connection.validation.execute(Statement.FINDING_RESOLUTION_WRITE_FINDING_RESOLUTIONS_014,(resolution_id,finding_id,finding[0],action,actor.user_id,reason,new_run["id"]))
            append_event_tx(connection,"finding_resolved","validation_finding",finding_id,actor_id=actor.user_id,organization_id=finding[5],contract_id=connection.invoices.execute(Statement.FINDING_RESOLUTION_READ_INVOICE_VERSIONS_007,(finding[0],)).fetchone()[0],payload={"action":action,"reason":reason,"newValidationRunId":new_run["id"],"resolutionId":resolution_id})
            connection.commit()
        return {"id":resolution_id,"priorFindingId":finding_id,"action":action,"reason":reason,"newValidationRunId":new_run["id"],"findings":current_findings(actor,finding[0]),"hasOpenBlockers":has_open_blockers(finding[0])}
    return execute_authorized(actor,Action.UPDATE,invoice_scope(actor,finding[0]),command)
