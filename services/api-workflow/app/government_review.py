from .authorization import Actor,ForbiddenError,Role
from .runtime import database

def _government(actor:Actor):
    if actor.role is not Role.GOVERNMENT_REVIEWER:raise ForbiddenError("Government queue is restricted to Government Reviewer")

def list_queue(actor:Actor)->list[dict]:
    _government(actor)
    with database() as connection:
        rows=connection.execute("""select q.id,q.status,o.name,c.name,iv.version,iv.total,s.submitted_at,s.id,p.id,p.zip_artifact_id,
                 cv.payload->'servicePeriod',count(vf.id) filter(where vf.status='open')
          from government_queue_items q join submissions s on s.id=q.submission_id join invoice_versions iv on iv.id=s.invoice_version_id
          join contracts c on c.id=iv.contract_id join organizations o on o.id=q.ngo_organization_id join packages p on p.id=s.package_id
          join configuration_versions cv on cv.id=iv.configuration_version_id
          left join validation_findings vf on vf.invoice_version_id=iv.id
          where q.agency_organization_id=%s group by q.id,o.name,c.name,iv.version,iv.total,s.submitted_at,s.id,p.id,p.zip_artifact_id,cv.payload order by s.submitted_at""",(actor.organization_id,)).fetchall()
    return [{"id":r[0],"status":r[1],"ngo":r[2],"contract":r[3],"invoiceVersion":r[4],"amount":str(r[5]),"submittedAt":r[6].isoformat(),"submissionId":r[7],"packageId":r[8],"zipArtifactId":r[9],"servicePeriod":r[10],"openFindingCount":r[11]} for r in rows]

def review_context(actor:Actor,queue_id:str)->dict:
    _government(actor)
    with database() as connection:
        row=connection.execute("""select q.status,s.invoice_version_id,s.package_id,p.zip_artifact_id,s.package_hashes,iv.configuration_version_id,iv.version,iv.total,o.name,c.name,s.submitted_at
          from government_queue_items q join submissions s on s.id=q.submission_id join packages p on p.id=s.package_id join invoice_versions iv on iv.id=s.invoice_version_id join organizations o on o.id=q.ngo_organization_id join contracts c on c.id=iv.contract_id
          where q.id=%s and q.agency_organization_id=%s""",(queue_id,actor.organization_id)).fetchone()
        if not row:raise FileNotFoundError(queue_id)
        run=connection.execute("select id,engine_version,input_hash,output_hash from validation_runs where invoice_version_id=%s order by created_at desc limit 1",(row[1],)).fetchone()
        findings=connection.execute("select code,severity,message,status,expense_key from validation_findings where validation_run_id=%s order by code",(run[0],)).fetchall()
        artifacts=connection.execute("select pa.path,pa.artifact_id,pa.sha256,a.media_type from package_artifacts pa join artifacts a on a.id=pa.artifact_id where pa.package_id=%s order by pa.path",(row[2],)).fetchall()
        events=connection.execute("select event_type,actor_id,occurred_at,payload from domain_events where aggregate_id in (%s,%s,%s) order by occurred_at,id",(row[1],row[2],queue_id)).fetchall()
    return {"queueId":queue_id,"status":row[0],"invoiceVersionId":row[1],"packageId":row[2],"zipArtifactId":row[3],"packageHashes":row[4],"configurationVersionId":row[5],"invoiceVersion":row[6],"amount":str(row[7]),"ngo":row[8],"contract":row[9],"submittedAt":row[10].isoformat(),"validation":{"id":run[0],"engineVersion":run[1],"inputHash":run[2],"outputHash":run[3]},"findings":[{"code":x[0],"severity":x[1],"message":x[2],"status":x[3],"expenseKey":x[4]} for x in findings],"artifacts":[{"path":x[0],"artifactId":x[1],"sha256":x[2],"mediaType":x[3]} for x in artifacts],"provenance":[{"eventType":x[0],"actorId":x[1],"occurredAt":x[2].isoformat(),"payload":x[3]} for x in events]}
