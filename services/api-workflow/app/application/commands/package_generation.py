from csv import DictWriter
from hashlib import sha256
from io import BytesIO, StringIO
import json, uuid, zipfile

from .artifacts import download_artifact, store_artifact
from .attestation import current_attestation
from .access_scope import invoice_scope
from ...authorization import Action, Actor, ResourceKind, execute_authorized
from .invoice_draft import get_draft
from .invoice_snapshots import create_invoice_snapshot_tx
from .provenance import append_event_tx, append_relation_tx

from ..package_rendering import render_invoice_pdf
from ..ports.statements import Statement
from ..transaction import transaction as database
class PackageError(ValueError): pass

def _json(value): return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()

def generate_package(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        row=connection.invoices.execute(Statement.PACKAGE_GENERATION_READ_INVOICE_VERSIONS_001,(invoice_id,)).fetchone()
    if not row: raise FileNotFoundError(invoice_id)
    scope=invoice_scope(actor,invoice_id,kind=ResourceKind.PACKAGE)
    def command():
        att=current_attestation(actor,invoice_id)
        if not att or not att["current"]: raise PackageError("A current exact-version attestation is required")
        invoice=get_draft(actor,invoice_id)
        with database() as connection:
            run=connection.validation.execute(Statement.PACKAGE_GENERATION_READ_VALIDATION_RUNS_002,(att["validationRunId"],)).fetchone()
        validation={"runId":run[0],"engineVersion":run[1],"inputHash":run[2],"outputHash":run[3]}
        claims=[];evidence={}
        for line in invoice["lines"]:
            claims.append({"expenseKey":line["expenseKey"],"amount":line["amount"],"ledgerArtifactId":line["ledgerArtifactId"],"ledgerSource":line["ledgerSource"],"evidenceArtifactId":line["evidenceArtifactId"],"extractionStatus":line["extractionStatus"],"validationRunId":run[0],"configurationVersionId":invoice["configurationVersionId"],"invoiceVersionId":invoice_id})
            if line["evidenceArtifactId"] and line["evidenceArtifactId"] not in evidence:evidence[line["evidenceArtifactId"]]=download_artifact(actor,line["evidenceArtifactId"])
        package_id=f"package-{uuid.uuid4().hex}";base={"packageId":package_id,"invoiceVersionId":invoice_id,"invoiceVersion":invoice["version"],"attestationId":att["id"],"claims":claims}
        csv_out=StringIO();writer=DictWriter(csv_out,fieldnames=list(claims[0]));writer.writeheader();writer.writerows(claims)
        files={"invoice.pdf":render_invoice_pdf(invoice),"validation-summary.json":_json(validation),"manifest.csv":csv_out.getvalue().encode()}
        for artifact_id,content in sorted(evidence.items()):files[f"evidence/{artifact_id}"]=content
        manifest={**base,"files":[{"path":p,"sha256":sha256(b).hexdigest(),"byteSize":len(b)} for p,b in sorted(files.items())]};files["manifest.json"]=_json(manifest)
        stored={p:store_artifact(actor,row[1],p.split("/")[-1],"application/pdf" if p.endswith(".pdf") else "application/json" if p.endswith(".json") else "text/csv" if p.endswith(".csv") else "application/octet-stream",b,artifact_kind="generated") for p,b in files.items()}
        zip_out=BytesIO()
        with zipfile.ZipFile(zip_out,"w",zipfile.ZIP_DEFLATED) as z:
            for path,content in sorted(files.items()):info=zipfile.ZipInfo(path,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,content)
        zip_art=store_artifact(actor,row[1],f"invoice-v{invoice['version']}-package.zip","application/zip",zip_out.getvalue(),artifact_kind="generated")
        with database() as connection:
            snapshot=create_invoice_snapshot_tx(connection,actor,invoice_id,"package")
            connection.packages.execute(Statement.PACKAGE_GENERATION_WRITE_PACKAGES_003,(package_id,invoice_id,att["id"],invoice["version"],zip_art.id,json.dumps(manifest),actor.user_id,snapshot["id"]))
            append_relation_tx(connection,row[1],row[0],"derived_from",
                {"kind":"package","id":package_id,"version":invoice["version"]},
                {"kind":"invoice_snapshot","id":snapshot["id"],"version":snapshot["payload"]["materialRevision"],"sha256":snapshot["sha256"]},actor=actor)
            for path,artifact in stored.items():connection.packages.execute(Statement.PACKAGE_GENERATION_WRITE_PACKAGE_ARTIFACTS_004,(package_id,artifact.id,path,artifact.sha256))
            connection.packages.execute(Statement.PACKAGE_GENERATION_WRITE_PACKAGE_ARTIFACTS_004,(package_id,zip_art.id,"package.zip",zip_art.sha256))
            append_event_tx(connection,"package_generated","package",package_id,actor_id=actor.user_id,organization_id=row[0],contract_id=row[1],payload={"invoiceVersionId":invoice_id,"zipArtifactId":zip_art.id,"zipSha256":zip_art.sha256,"invoiceSnapshotId":snapshot["id"]},version_references=[
                {"kind":"package","id":package_id,"version":invoice["version"]},
                {"kind":"invoice_snapshot","id":snapshot["id"],"version":snapshot["payload"]["materialRevision"],"sha256":snapshot["sha256"]},
                {"kind":"artifact","id":zip_art.id,"version":1,"sha256":zip_art.sha256},
            ]);connection.commit()
        return {"id":package_id,"invoiceVersionId":invoice_id,"manifest":manifest,"artifacts":{p:{"id":a.id,"sha256":a.sha256} for p,a in stored.items()},"zip":{"id":zip_art.id,"sha256":zip_art.sha256}}
    return execute_authorized(actor,Action.SUBMIT,scope,command)
