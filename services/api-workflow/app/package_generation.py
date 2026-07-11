from csv import DictWriter
from hashlib import sha256
from io import BytesIO, StringIO
import json, uuid, zipfile

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .artifacts import download_artifact, store_artifact
from .attestation import current_attestation
from .authorization import Action, Actor, ResourceKind, ResourceScope, execute_authorized
from .invoice_draft import get_draft
from .provenance import append_event_tx
from .runtime import database

class PackageError(ValueError): pass

def _json(value): return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()

def _pdf(invoice):
    out=BytesIO();doc=SimpleDocTemplate(out,pagesize=LETTER,title=f"Invoice v{invoice['version']}",author="ContractView POC",invariant=1)
    styles=getSampleStyleSheet();story=[Paragraph("Reimbursement Invoice",styles["Title"]),Paragraph(f"Invoice version {invoice['version']} | Configuration {invoice['configurationVersionId']}",styles["Normal"]),Spacer(1,12)]
    rows=[["Expense","Date","Vendor","Category","Amount"]]+[[x["expenseKey"],x["date"],x["vendor"],x["category"],f"${x['amount']}"] for x in invoice["lines"]]
    table=Table(rows,repeatRows=1,colWidths=[60,65,150,100,65]);table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#294d37")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.5,colors.grey),("FONTSIZE",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP"),("ALIGN",(-1,1),(-1,-1),"RIGHT")]))
    story += [table,Spacer(1,14),Paragraph(f"Total requested: ${invoice['total']}",styles["Heading2"]),Paragraph("Synthetic demonstration data only",styles["Italic"])]
    doc.build(story);return out.getvalue()

def generate_package(actor:Actor,invoice_id:str)->dict:
    with database() as connection:
        row=connection.execute("select organization_id,contract_id,version from invoice_versions where id=%s",(invoice_id,)).fetchone()
    if not row: raise FileNotFoundError(invoice_id)
    scope=ResourceScope(invoice_id,ResourceKind.PACKAGE,row[0],ngo_organization_id=row[0])
    def command():
        att=current_attestation(actor,invoice_id)
        if not att or not att["current"]: raise PackageError("A current exact-version attestation is required")
        invoice=get_draft(actor,invoice_id)
        with database() as connection:
            run=connection.execute("select id,engine_version,input_hash,output_hash from validation_runs where id=%s",(att["validationRunId"],)).fetchone()
        validation={"runId":run[0],"engineVersion":run[1],"inputHash":run[2],"outputHash":run[3]}
        claims=[];evidence={}
        for line in invoice["lines"]:
            claims.append({"expenseKey":line["expenseKey"],"amount":line["amount"],"ledgerArtifactId":line["ledgerArtifactId"],"ledgerSource":line["ledgerSource"],"evidenceArtifactId":line["evidenceArtifactId"],"extractionStatus":line["extractionStatus"],"validationRunId":run[0],"configurationVersionId":invoice["configurationVersionId"],"invoiceVersionId":invoice_id})
            if line["evidenceArtifactId"] and line["evidenceArtifactId"] not in evidence:evidence[line["evidenceArtifactId"]]=download_artifact(actor,line["evidenceArtifactId"])
        package_id=f"package-{uuid.uuid4().hex}";base={"packageId":package_id,"invoiceVersionId":invoice_id,"invoiceVersion":invoice["version"],"attestationId":att["id"],"claims":claims}
        csv_out=StringIO();writer=DictWriter(csv_out,fieldnames=list(claims[0]));writer.writeheader();writer.writerows(claims)
        files={"invoice.pdf":_pdf(invoice),"validation-summary.json":_json(validation),"manifest.csv":csv_out.getvalue().encode()}
        for artifact_id,content in sorted(evidence.items()):files[f"evidence/{artifact_id}"]=content
        manifest={**base,"files":[{"path":p,"sha256":sha256(b).hexdigest(),"byteSize":len(b)} for p,b in sorted(files.items())]};files["manifest.json"]=_json(manifest)
        stored={p:store_artifact(actor,row[1],p.split("/")[-1],"application/pdf" if p.endswith(".pdf") else "application/json" if p.endswith(".json") else "text/csv" if p.endswith(".csv") else "application/octet-stream",b,artifact_kind="generated") for p,b in files.items()}
        zip_out=BytesIO()
        with zipfile.ZipFile(zip_out,"w",zipfile.ZIP_DEFLATED) as z:
            for path,content in sorted(files.items()):info=zipfile.ZipInfo(path,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,content)
        zip_art=store_artifact(actor,row[1],f"invoice-v{invoice['version']}-package.zip","application/zip",zip_out.getvalue(),artifact_kind="generated")
        with database() as connection:
            connection.execute("insert into packages(id,invoice_version_id,attestation_id,version,zip_artifact_id,manifest,created_by) values (%s,%s,%s,%s,%s,%s,%s)",(package_id,invoice_id,att["id"],invoice["version"],zip_art.id,json.dumps(manifest),actor.user_id))
            for path,artifact in stored.items():connection.execute("insert into package_artifacts values (%s,%s,%s,%s)",(package_id,artifact.id,path,artifact.sha256))
            connection.execute("insert into package_artifacts values (%s,%s,%s,%s)",(package_id,zip_art.id,"package.zip",zip_art.sha256))
            append_event_tx(connection,"package_generated","package",package_id,actor_id=actor.user_id,organization_id=row[0],contract_id=row[1],payload={"invoiceVersionId":invoice_id,"zipArtifactId":zip_art.id,"zipSha256":zip_art.sha256});connection.commit()
        return {"id":package_id,"invoiceVersionId":invoice_id,"manifest":manifest,"artifacts":{p:{"id":a.id,"sha256":a.sha256} for p,a in stored.items()},"zip":{"id":zip_art.id,"sha256":zip_art.sha256}}
    return execute_authorized(actor,Action.SUBMIT,scope,command)
