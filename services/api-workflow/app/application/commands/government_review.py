from ...authorization import Actor,ForbiddenError,Role

from ..ports.statements import Statement
from ..transaction import transaction as database
def _government(actor:Actor):
    if actor.role is not Role.GOVERNMENT_REVIEWER:raise ForbiddenError("Government queue is restricted to Government Reviewer")

def list_queue(actor:Actor)->list[dict]:
    _government(actor)
    with database() as connection:
        rows=connection.read_models.execute(Statement.GOVERNMENT_REVIEW_READ_CONFIGURATION_VERSIONS_CONTRACTS_GOVERNMENT_QUEUE_ITEMS_INVOICE_VERSIONS_001,(actor.organization_id,)).fetchall()
    return [{"id":r[0],"status":r[1],"ngo":r[2],"contract":r[3],"invoiceVersion":r[4],"amount":str(r[5]),"submittedAt":r[6].isoformat(),"submissionId":r[7],"packageId":r[8],"zipArtifactId":r[9],"servicePeriod":r[10],"openFindingCount":r[11]} for r in rows]

def review_context(actor:Actor,queue_id:str)->dict:
    _government(actor)
    with database() as connection:
        row=connection.read_models.execute(Statement.GOVERNMENT_REVIEW_READ_CONTRACTS_GOVERNMENT_QUEUE_ITEMS_INVOICE_VERSIONS_ORGANIZATIONS_002,(queue_id,actor.organization_id)).fetchone()
        if not row:raise FileNotFoundError(queue_id)
        run=connection.validation.execute(Statement.GOVERNMENT_REVIEW_READ_VALIDATION_RUNS_003,(row[1],)).fetchone()
        if not run:raise RuntimeError("Submitted invoice is missing validation evidence")
        findings=connection.validation.execute(Statement.GOVERNMENT_REVIEW_READ_VALIDATION_FINDINGS_004,(run[0],)).fetchall()
        artifacts=connection.read_models.execute(Statement.GOVERNMENT_REVIEW_READ_ARTIFACTS_PACKAGE_ARTIFACTS_005,(row[2],)).fetchall()
        events=connection.provenance.execute(Statement.GOVERNMENT_REVIEW_READ_DOMAIN_EVENTS_006,(row[1],row[2],queue_id)).fetchall()
    return {"queueId":queue_id,"status":row[0],"invoiceVersionId":row[1],"packageId":row[2],"zipArtifactId":row[3],"packageHashes":row[4],"configurationVersionId":row[5],"invoiceVersion":row[6],"amount":str(row[7]),"ngo":row[8],"contract":row[9],"submittedAt":row[10].isoformat(),"validation":{"id":run[0],"engineVersion":run[1],"inputHash":run[2],"outputHash":run[3]},"findings":[{"code":x[0],"severity":x[1],"message":x[2],"status":x[3],"expenseKey":x[4]} for x in findings],"artifacts":[{"path":x[0],"artifactId":x[1],"sha256":x[2],"mediaType":x[3]} for x in artifacts],"provenance":[{"eventType":x[0],"actorId":x[1],"occurredAt":x[2].isoformat(),"payload":x[3]} for x in events]}
