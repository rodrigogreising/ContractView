import ast
import json
from hashlib import sha256
from decimal import Decimal
from pathlib import Path

import pytest
import psycopg

from app.artifacts import store_artifact
from app.authorization import Action,Actor,ForbiddenError,Role,is_allowed
from app.access_scope import government_decision_scope
from app.configuration import update_draft
from configuration_helpers import ensure_active_configuration
from app.extraction import OcrResponse
from app.extraction_review import list_extractions,review_field
from app.ingestion import claim_next_job,create_upload_job,process_job
from app.invoice_draft import assemble_draft,get_draft
from app.runtime import database
from app.validation import ENGINE_VERSION,execute_validation,reproduce_validation
from app.budget import budget_snapshot
from app.finding_resolution import current_findings,has_open_blockers,resolve_finding
from app.attestation import ATTESTATION_TEXT,AttestationError,approval_preview,attest,current_attestation
from app.package_generation import PackageError,generate_package,reproduce_package
from app.submission import submit
from app.government_review import list_queue,review_context
from app.government_decision import DecisionError,decide
from app.revision import correct_revision,revision_feedback
from app.provenance import audit_query
from app.artifacts import download_artifact
from io import BytesIO
import zipfile

CONTRACT="contract-synthetic-agency-ngo-2026";FILES=Path("/app/fixtures/files")
PREPARER=Actor("user-ngo-preparer","org-ngo",Role.NGO_PREPARER);APPROVER=Actor("user-ngo-approver","org-ngo",Role.NGO_APPROVER);ADMIN=Actor("user-config-admin","org-operations",Role.CONFIGURATION_ADMINISTRATOR)
AUDITOR=Actor("user-auditor","org-oversight",Role.AUDITOR)


def canonical_hash(value):
    encoded=json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    return sha256(encoded).hexdigest()

class Adapter:
    provider="validation-fixture-provider";model="validation-fixture-v1"
    def extract(self,*_):return OcrResponse(self.provider,self.model,"Synthetic Program Supplies Vendor B\nDate: 2026-06-18\nWorkshop materials and learning kits $1,820.00\nExpense reference: VENDOR-INVOICE-EXP-003\n",Decimal("0.9500"))

def complete(job,adapter=None):
    if job.status=="completed":return
    claimed=claim_next_job();assert claimed and claimed.id==job.id;process_job(claimed,adapter)

@pytest.fixture(scope="module")
def invoice():
    payload=json.loads(Path("/app/fixtures/scenario.json").read_text())["initialConfiguration"];update_draft(ADMIN,CONTRACT,payload);ensure_active_configuration(ADMIN,CONTRACT)
    complete(create_upload_job(PREPARER,CONTRACT,"validation-ledger.csv","text/csv",(FILES/"ledger-june-2026.csv").read_bytes()))
    for filename in ("payroll-june-2026.xlsx","vendor-invoice-exp-002.pdf","vendor-invoice-exp-004.png","vendor-invoice-exp-005.pdf"):
        media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filename.endswith("xlsx") else "image/png" if filename.endswith("png") else "application/pdf";store_artifact(PREPARER,CONTRACT,filename,media,(FILES/filename).read_bytes())
    job=create_upload_job(PREPARER,CONTRACT,"vendor-invoice-exp-003.pdf","application/pdf",(FILES/"vendor-invoice-exp-003.pdf").read_bytes());complete(job,Adapter())
    extraction=next(item for item in list_extractions(PREPARER,CONTRACT) if item["filename"]=="vendor-invoice-exp-003.pdf");amount=next(field for field in extraction["fields"] if field["name"]=="amount")
    if amount["reviewStatus"]=="proposed":review_field(PREPARER,amount["id"],"correct","1280.00","Approved claim total")
    return assemble_draft(PREPARER,CONTRACT)

def test_five_rules_record_versions_inputs_results_and_expected_findings(invoice):
    run=execute_validation(PREPARER,invoice["id"])
    assert run["engineVersion"]==ENGINE_VERSION and run["invoiceVersionId"]==invoice["id"] and run["configurationVersionId"]==invoice["configurationVersionId"]
    assert len(run["inputHash"])==64 and len(run["outputHash"])==64
    assert run["inputManifestId"].startswith("validation-input-")
    assert run["inputManifestHash"]==run["inputHash"]
    assert {item["ruleCode"] for item in run["results"]}=={"SERVICE_PERIOD","REQUIRED_EVIDENCE","BUDGET_AVAILABLE","TOTAL_RECONCILIATION","POSSIBLE_DUPLICATE"}
    assert all(item["ruleVersion"] and item["severity"] in {"blocker","warning"} and item["normalizedInput"] for item in run["results"])
    failures={item["reasonCode"]:item for item in run["results"] if item["outcome"]=="fail"}
    assert set(failures)=={"SERVICE_PERIOD:EXP-004","POSSIBLE_DUPLICATE:EXP-005:EXP-002"}
    assert failures["SERVICE_PERIOD:EXP-004"]["severity"]=="blocker" and failures["POSSIBLE_DUPLICATE:EXP-005:EXP-002"]["severity"]=="warning"
    with database() as connection:
        event=connection.execute("select event_type,payload->>'inputHash',payload->>'outputHash' from domain_events where aggregate_id=%s",(run["id"],)).fetchone()
        manifest=connection.execute("select manifest,manifest_hash from validation_input_manifests where id=%s",(run["inputManifestId"],)).fetchone()
    assert event==("validation_completed",run["inputHash"],run["outputHash"])
    assert manifest[1]==run["inputHash"]
    assert {"invoiceSnapshot","artifacts","schemas","mappings","rules","workflow","views","templates","configurationVersion","extractionComponents"} <= set(manifest[0])
    assert manifest[0]["engineVersion"]==ENGINE_VERSION
    assert all(item["version"] for item in manifest[0]["rules"])

def test_same_invoice_and_configuration_reproduce_identical_normalized_output(invoice):
    first=execute_validation(PREPARER,invoice["id"]);second=execute_validation(PREPARER,invoice["id"])
    assert first["id"]!=second["id"]
    assert first["normalizedInputs"]==second["normalizedInputs"]
    assert first["inputHash"]==second["inputHash"] and first["outputHash"]==second["outputHash"]
    assert first["inputManifestId"]==second["inputManifestId"]
    assert first["results"]==second["results"]
    reproduced=reproduce_validation(PREPARER,first["id"])
    assert reproduced["matches"] and reproduced["inputHash"]==first["inputHash"]
    assert reproduced["outputHash"]==first["outputHash"] and reproduced["results"]==first["results"]

def test_non_preparer_cannot_create_validation_run(invoice):
    with database() as connection:before=connection.execute("select count(*) from validation_runs where engine_version is not null").fetchone()[0]
    with pytest.raises(ForbiddenError):execute_validation(APPROVER,invoice["id"])
    with database() as connection:after=connection.execute("select count(*) from validation_runs where engine_version is not null").fetchone()[0]
    assert after==before

def test_validation_module_has_no_ai_or_extraction_dependency():
    source=Path("/app/app/validation.py").read_text()
    tree=ast.parse(source)
    imports={node.module or "" for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
    imports.update(alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names)
    forbidden=("extraction","openai","anthropic","ollama")
    assert not any(token in module.lower() for module in imports for token in forbidden)
    assert "prompt" not in source.lower()

def test_versioned_budget_snapshot_is_visible_to_ngo_and_submitted_government(invoice):
    ngo=budget_snapshot(PREPARER,invoice["id"])
    assert ngo["configurationVersionId"]==invoice["configurationVersionId"]
    assert ngo["total"]=={"requested":"10130.00","budgeted":"96000.00","remaining":"85870.00","overBudget":False}
    government=Actor("user-government-reviewer","org-government",Role.GOVERNMENT_REVIEWER)
    with pytest.raises(ForbiddenError):budget_snapshot(government,invoice["id"])
    with database() as connection:connection.execute("update invoice_versions set state='submitted' where id=%s",(invoice["id"],));connection.commit()
    assert budget_snapshot(government,invoice["id"])["total"]==ngo["total"]
    with database() as connection:connection.execute("update invoice_versions set state='draft' where id=%s",(invoice["id"],));connection.commit()

def test_blocker_correction_and_warning_dismissal_preserve_history_and_new_runs(invoice):
    execute_validation(PREPARER,invoice["id"])
    findings={item["code"]:item for item in current_findings(PREPARER,invoice["id"])}
    blocker=findings["SERVICE_PERIOD:EXP-004"];warning=findings["POSSIBLE_DUPLICATE:EXP-005:EXP-002"]
    assert blocker["expenseKey"]=="EXP-004" and blocker["evidenceArtifactId"] and "Correct the service date" in blocker["remediation"]
    assert has_open_blockers(invoice["id"])
    with pytest.raises(ForbiddenError):resolve_finding(APPROVER,blocker["id"],"correct","not authorized","2026-06-30")
    with database() as connection:assert connection.execute("select count(*) from finding_resolutions where prior_finding_id=%s",(blocker["id"],)).fetchone()[0]==0
    corrected=resolve_finding(PREPARER,blocker["id"],"correct","Service occurred on the documented June date","2026-06-30")
    assert corrected["priorFindingId"]==blocker["id"] and corrected["newValidationRunId"] and not corrected["hasOpenBlockers"]
    current={item["code"]:item for item in corrected["findings"]}
    assert "SERVICE_PERIOD:EXP-004" not in current
    warning=current["POSSIBLE_DUPLICATE:EXP-005:EXP-002"]
    dismissed=resolve_finding(PREPARER,warning["id"],"dismiss","Different facility service occurrence; retain for reviewer visibility")
    assert not dismissed["hasOpenBlockers"]
    latest={item["code"]:item for item in dismissed["findings"]}
    assert latest["POSSIBLE_DUPLICATE:EXP-005:EXP-002"]["status"]=="dismissed"
    with database() as connection:
        correction=connection.execute("select prior_value,corrected_value,actor_id,reason,created_at is not null from invoice_line_corrections where invoice_version_id=%s",(invoice["id"],)).fetchone()
        resolutions=connection.execute("select action,actor_id,reason,new_validation_run_id,created_at is not null from finding_resolutions where invoice_version_id=%s order by created_at",(invoice["id"],)).fetchall()
        historical=connection.execute("select count(*) from validation_results where reason_code='POSSIBLE_DUPLICATE:EXP-005:EXP-002' and outcome='fail' and validation_run_id=%s",(dismissed["newValidationRunId"],)).fetchone()[0]
        events={row[0] for row in connection.execute("select event_type from domain_events where event_type in ('invoice_line_corrected','finding_resolved')").fetchall()}
        expense_date_chain=connection.execute("""select corrected.field_name,predecessor.field_name
            from field_lineage corrected join field_lineage predecessor on predecessor.id=corrected.predecessor_lineage_id
            where corrected.invoice_version_id=%s and corrected.field_name='EXP-004.expenseDate'
              and corrected.correction_actor_id=%s order by corrected.id desc limit 1""",(invoice["id"],PREPARER.user_id)).fetchone()
    assert correction==("2026-07-03","2026-06-30",PREPARER.user_id,"Service occurred on the documented June date",True)
    assert [row[0] for row in resolutions]==["correct","dismiss"] and all(row[1]==PREPARER.user_id and row[3] and row[4] for row in resolutions)
    assert historical==1 and events=={"invoice_line_corrected","finding_resolved"}
    assert expense_date_chain==("EXP-004.expenseDate","EXP-004.expenseDate")

def ensure_eligible(invoice):
    execute_validation(PREPARER,invoice["id"])
    findings=current_findings(PREPARER,invoice["id"])
    blocker=next((item for item in findings if item["severity"]=="blocker"),None)
    if blocker:resolve_finding(PREPARER,blocker["id"],"correct","Documented June service date","2026-06-30")
    warning=next((item for item in current_findings(PREPARER,invoice["id"]) if item["severity"]=="warning" and item["status"]=="open"),None)
    if warning:resolve_finding(PREPARER,warning["id"],"dismiss","Distinct service occurrence")

def test_exact_version_attestation_authority_freshness_and_staleness(invoice):
    ensure_eligible(invoice)
    preview=approval_preview(APPROVER,invoice["id"])
    assert preview["invoice"]["id"]==invoice["id"] and preview["invoice"]["total"]=="10130.00"
    assert preview["invoice"]["configurationVersionId"]==invoice["configurationVersionId"]
    assert preview["validationFresh"] and not preview["hasOpenBlockers"] and preview["validationOutputHash"]
    assert preview["packagePreview"]["evidenceCount"]==5 and "package.zip" in preview["packagePreview"]["files"]
    with pytest.raises(ForbiddenError):attest(PREPARER,invoice["id"],ATTESTATION_TEXT)
    with database() as connection:assert connection.execute("select count(*) from attestations where invoice_version_id=%s",(invoice["id"],)).fetchone()[0]==0
    record=attest(APPROVER,invoice["id"],ATTESTATION_TEXT)
    assert record["current"] and record["actorId"]==APPROVER.user_id and record["actorRole"]==Role.NGO_APPROVER.value
    assert record["attestationVersion"]=="ngo-approver-attestation-v1" and record["attestationText"]==ATTESTATION_TEXT and record["createdAt"] and len(record["fingerprint"])==64
    with database() as connection:
        event=connection.execute("select event_type,payload->>'attestationId',payload->>'fingerprint' from domain_events where event_type='attested' and aggregate_id=%s order by id desc limit 1",(invoice["id"],)).fetchone()
        connection.execute("update invoice_versions set material_revision=material_revision+1 where id=%s",(invoice["id"],));connection.commit()
    assert event==("attested",record["id"],record["fingerprint"])
    assert not current_attestation(APPROVER,invoice["id"])["current"]
    assert not approval_preview(APPROVER,invoice["id"])["validationFresh"]
    with pytest.raises(AttestationError,match="fresh validation"):attest(APPROVER,invoice["id"],ATTESTATION_TEXT)
    execute_validation(PREPARER,invoice["id"])
    replacement=attest(APPROVER,invoice["id"],ATTESTATION_TEXT)
    assert replacement["current"] and replacement["id"]!=record["id"] and replacement["materialRevision"]==record["materialRevision"]+1

def test_real_immutable_package_has_pdf_manifests_evidence_zip_and_hashes(invoice):
    with pytest.raises(ForbiddenError):generate_package(PREPARER,invoice["id"])
    package=generate_package(APPROVER,invoice["id"])
    assert package["invoiceVersionId"]==invoice["id"] and package["manifest"]["attestationId"]
    assert {"invoice.pdf","validation-summary.json","manifest.json","manifest.csv"}.issubset(package["artifacts"])
    assert download_artifact(APPROVER,package["artifacts"]["invoice.pdf"]["id"]).startswith(b"%PDF")
    zip_bytes=download_artifact(APPROVER,package["zip"]["id"])
    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        names=set(archive.namelist());assert {"invoice.pdf","validation-summary.json","manifest.json","manifest.csv"}.issubset(names)
        assert len([name for name in names if name.startswith("evidence/")])==5
        for item in package["manifest"]["files"]:assert sha256(archive.read(item["path"])).hexdigest()==item["sha256"]
    with database() as connection:
        records=connection.execute("select path,sha256 from package_artifacts where package_id=%s",(package["id"],)).fetchall()
        event=connection.execute("select payload->>'zipSha256',payload->>'reproductionManifestHash' from domain_events where aggregate_id=%s and event_type='package_generated'",(package["id"],)).fetchone()
        persisted=connection.execute("select build_input_hash,reproduction_manifest_hash,archive_sha256,archive_byte_size from package_reproduction_manifests where package_id=%s",(package["id"],)).fetchone()
    assert len(records)==len(package["artifacts"])+1 and all(len(row[1])==64 for row in records)
    assert event==(package["zip"]["sha256"],package["reproduction"]["manifestHash"])
    assert persisted==(package["reproduction"]["buildInputHash"],package["reproduction"]["manifestHash"],package["zip"]["sha256"],len(zip_bytes))
    reproduced=reproduce_package(APPROVER,package["id"])
    assert reproduced["fileChecks"]=={key:True for key in reproduced["fileChecks"]}
    assert reproduced["checks"]=={key:True for key in reproduced["checks"]}
    assert reproduced["matches"] and reproduced["archiveBytes"]==zip_bytes
    assert reproduced["archiveSha256"]==package["zip"]["sha256"]
    with pytest.raises(psycopg.errors.RaiseException,match="append-only"):
        with database() as connection:connection.execute("update package_reproduction_manifests set build_input='{}' where package_id=%s",(package["id"],))

def test_submission_atomically_locks_exact_version_and_creates_government_queue(invoice):
    with database() as connection:
        before=connection.execute("select count(*) from submissions").fetchone()[0]
    with pytest.raises(ForbiddenError):submit(PREPARER,invoice["id"])
    with database() as connection:assert connection.execute("select count(*) from submissions").fetchone()[0]==before
    submission=submit(APPROVER,invoice["id"])
    assert submission["state"]=="submitted" and submission["invoiceVersion"]==invoice["version"] and submission["configurationVersionId"]==invoice["configurationVersionId"]
    assert "package.zip" in submission["packageHashes"] and all(len(value)==64 for value in submission["packageHashes"].values())
    with database() as connection:
        row=connection.execute("select i.state,q.status,s.actor_id,s.actor_role,s.submitted_at is not null from submissions s join invoice_versions i on i.id=s.invoice_version_id join government_queue_items q on q.submission_id=s.id where s.id=%s",(submission["id"],)).fetchone()
        published=connection.execute("select bool_and(a.submitted) from package_artifacts p join artifacts a on a.id=p.artifact_id where p.package_id=%s",(submission["packageId"],)).fetchone()[0]
        submitted_sources=connection.execute("""select distinct a.id,a.submitted from artifacts a where a.id in (
          select ledger_artifact_id from invoice_lines where invoice_version_id=%s
          union select evidence_artifact_id from invoice_lines where invoice_version_id=%s and evidence_artifact_id is not null
          union select x.source_artifact_id from invoice_lines l join extraction_fields f on f.id=l.extraction_field_id join extraction_runs x on x.id=f.extraction_run_id where l.invoice_version_id=%s
          union select x.raw_response_artifact_id from invoice_lines l join extraction_fields f on f.id=l.extraction_field_id join extraction_runs x on x.id=f.extraction_run_id where l.invoice_version_id=%s and x.raw_response_artifact_id is not null
        ) order by a.id""",(invoice["id"],invoice["id"],invoice["id"],invoice["id"])).fetchall()
        event=connection.execute("select payload->>'submissionId',payload->>'packageId' from domain_events where event_type='submitted' and aggregate_id=%s",(invoice["id"],)).fetchone()
        snapshot_links=connection.execute("""select
            (select s.stage from validation_runs r join invoice_snapshots s on s.id=r.invoice_snapshot_id where r.invoice_version_id=%s order by r.created_at desc limit 1),
            (select s.stage from attestations a join invoice_snapshots s on s.id=a.invoice_snapshot_id where a.invoice_version_id=%s order by a.created_at desc limit 1),
            (select s.stage from packages p join invoice_snapshots s on s.id=p.invoice_snapshot_id where p.id=%s),
            (select s.stage from submissions u join invoice_snapshots s on s.id=u.invoice_snapshot_id where u.id=%s)
        """,(invoice["id"],invoice["id"],submission["packageId"],submission["id"])).fetchone()
    assert row==("submitted","submitted",APPROVER.user_id,Role.NGO_APPROVER.value,True) and published
    assert submitted_sources and all(item[1] for item in submitted_sources)
    assert all(download_artifact(AUDITOR,item[0]) for item in submitted_sources)
    auditor_evidence=audit_query(AUDITOR,CONTRACT,submitted=True)
    assert {"extraction_drafted","field_reviewed","validation_completed","attested","package_generated","submitted"} <= {item["eventType"] for item in auditor_evidence["events"]}
    assert any(item["invoiceVersionId"]==invoice["id"] for item in auditor_evidence["lineage"])
    assert event==(submission["id"],submission["packageId"])
    assert snapshot_links==("validation","attestation","package","submission")
    invoice_snapshots=[item for item in auditor_evidence["snapshots"] if item["invoiceVersionId"]==invoice["id"]]
    assert {item["stage"] for item in invoice_snapshots}=={"validation","attestation","package","submission"}
    assert all(item["snapshotHash"]==canonical_hash(item["payload"]) for item in invoice_snapshots)
    assert {"supports","maps_to","validated_by","derived_from","submitted_as"} <= {
        item["relationType"] for item in auditor_evidence["relations"]
    }
    with pytest.raises(Exception,match="submitted invoice content is immutable"):
        with database() as connection:connection.execute("update invoice_lines set claimed_amount=1 where invoice_version_id=%s",(invoice["id"],))

    government=Actor("user-government-reviewer","org-government",Role.GOVERNMENT_REVIEWER)
    with pytest.raises(ForbiddenError):list_queue(PREPARER)
    queue=list_queue(government);item=next(x for x in queue if x["id"]==submission["queueItemId"])
    unpublished=government_decision_scope(PREPARER,item["id"])
    assert not unpublished.published_to_ngo and not is_allowed(PREPARER,Action.READ,unpublished)
    assert item["status"]=="submitted" and item["ngo"]=="Synthetic Community Nonprofit" and item["invoiceVersion"]==invoice["version"]
    assert item["amount"]==invoice["total"] and item["servicePeriod"]=={"start":"2026-06-01","end":"2026-06-30"} and item["submittedAt"]
    context=review_context(government,item["id"])
    assert context["packageId"]==submission["packageId"] and context["configurationVersionId"]==invoice["configurationVersionId"]
    assert context["validation"]["outputHash"] and context["findings"] and context["artifacts"]
    assert any(x["path"]=="package.zip" and x["artifactId"]==context["zipArtifactId"] for x in context["artifacts"])
    assert any(x["eventType"]=="submitted" for x in context["provenance"])
    assert list_queue(Actor("outside-reviewer","org-other",Role.GOVERNMENT_REVIEWER))==[]
    with pytest.raises(ForbiddenError):decide(PREPARER,item["id"],"returned","EVIDENCE_CORRECTION","Correct the service evidence",["EXP-004"])
    with database() as connection:
        decision_state_before=connection.execute("""select
            (select count(*) from government_decisions),
            (select count(*) from invoice_version_links),
            (select status from government_queue_items where id=%s),
            (select state from invoice_versions where id=%s)""",(item["id"],invoice["id"])).fetchone()
    with pytest.raises(DecisionError,match="at least one"):decide(government,item["id"],"returned","EVIDENCE_CORRECTION","Missing affected line",[])
    with pytest.raises(DecisionError,match="exact submitted invoice"):decide(government,item["id"],"returned","EVIDENCE_CORRECTION","Foreign affected line",["EXP-999"])
    with pytest.raises(DecisionError,match="unique"):decide(government,item["id"],"returned","EVIDENCE_CORRECTION","Duplicate affected line",["EXP-004","EXP-004"])
    with pytest.raises(DecisionError,match="return reason"):decide(government,item["id"],"returned","APPROVED_AS_CORRECTED","Wrong structured reason",["EXP-004"])
    with database() as connection:
        decision_state_after=connection.execute("""select
            (select count(*) from government_decisions),
            (select count(*) from invoice_version_links),
            (select status from government_queue_items where id=%s),
            (select state from invoice_versions where id=%s)""",(item["id"],invoice["id"])).fetchone()
    assert decision_state_after==decision_state_before
    with database() as connection:
        v1_snapshots_before=connection.execute("select id,material_revision,stage,payload,snapshot_hash from invoice_snapshots where invoice_version_id=%s order by material_revision,stage",(invoice["id"],)).fetchall()
    returned=decide(government,item["id"],"returned","EVIDENCE_CORRECTION","Correct the service evidence and resubmit",["EXP-004"])
    published_decision=government_decision_scope(PREPARER,item["id"])
    assert published_decision.published_to_ngo and is_allowed(PREPARER,Action.READ,published_decision)
    assert returned["decision"]=="returned" and returned["invoiceVersion"]==invoice["version"] and returned["actorRole"]==Role.GOVERNMENT_REVIEWER.value
    with pytest.raises(DecisionError,match="stale or out of order"):decide(government,item["id"],"approved","APPROVED_AS_CORRECTED","approve",[])
    with pytest.raises(DecisionError,match="provisioned human"):decide(Actor("system-ai","org-government",Role.GOVERNMENT_REVIEWER),item["id"],"returned","CLARIFICATION","system attempt",[])
    with database() as connection:
        decision_row=connection.execute("select decision,reason_code,note,line_keys,actor_id,actor_role,decided_at is not null from government_decisions where id=%s",(returned["id"],)).fetchone()
        decision_event=connection.execute("select actor_id,actor_role,actor_organization_id,organization_id,reason_code,payload->>'packageId',version_references from domain_events where event_type='returned' and aggregate_id=%s order by id desc limit 1",(invoice["id"],)).fetchone()
        state=connection.execute("select q.status,i.state from government_queue_items q join submissions s on s.id=q.submission_id join invoice_versions i on i.id=s.invoice_version_id where q.id=%s",(item["id"],)).fetchone()
    assert decision_row==("returned","EVIDENCE_CORRECTION","Correct the service evidence and resubmit",["EXP-004"],government.user_id,Role.GOVERNMENT_REVIEWER.value,True)
    assert decision_event[:6]==(government.user_id,Role.GOVERNMENT_REVIEWER.value,"org-government","org-ngo","EVIDENCE_CORRECTION",submission["packageId"])
    assert {reference["kind"] for reference in decision_event[6]}=={"invoice","submission","package","decision"}
    assert state==("returned","returned")
    successor=returned["successorInvoiceVersionId"];feedback=revision_feedback(PREPARER,CONTRACT)
    assert feedback["invoiceVersionId"]==successor and feedback["predecessorInvoiceVersionId"]==invoice["id"] and feedback["lineKeys"]==["EXP-004"]
    v2=get_draft(PREPARER,successor);assert v2["version"]==invoice["version"]+1 and v2["state"]=="draft" and v2["total"]==invoice["total"]
    with pytest.raises(ForbiddenError):correct_revision(APPROVER,successor,"EXP-004","Corrected evidence description","Government feedback")
    correction=correct_revision(PREPARER,successor,"EXP-004","Equipment rental supported by corrected June service evidence","Government feedback decision")
    assert correction["priorValue"]!=correction["correctedValue"]
    execute_validation(PREPARER,successor);v2_attestation=attest(APPROVER,successor,ATTESTATION_TEXT);assert v2_attestation["current"]
    v2_package=generate_package(APPROVER,successor);assert v2_package["zip"]["sha256"]!=submission["packageHashes"]["package.zip"]
    v2_submission=submit(APPROVER,successor);assert v2_submission["invoiceVersion"]==v2["version"]
    v2_item=next(x for x in list_queue(government) if x["id"]==v2_submission["queueItemId"]);assert v2_item["status"]=="submitted"
    approved=decide(government,v2_item["id"],"approved","APPROVED_AS_CORRECTED","Corrected evidence reviewed and approved",[])
    assert approved["decision"]=="approved" and approved["invoiceVersion"]==v2["version"] and approved["packageId"]==v2_package["id"]
    with database() as connection:
        v1_hashes=dict(connection.execute("select path,sha256 from package_artifacts where package_id=%s",(submission["packageId"],)).fetchall())
        reproduction_hashes=connection.execute("select package_id,build_input_hash,archive_sha256 from package_reproduction_manifests where package_id in (%s,%s) order by package_id",(submission["packageId"],v2_package["id"])).fetchall()
        link=connection.execute("select predecessor_invoice_version_id,successor_invoice_version_id,government_decision_id from invoice_version_links where successor_invoice_version_id=%s",(successor,)).fetchone()
        v1_feedback=connection.execute("select reason_code,note,line_keys from government_decisions where id=%s",(returned["id"],)).fetchone()
        final=connection.execute("select state from invoice_versions where id=%s",(successor,)).fetchone()[0]
        approval_event=connection.execute("select actor_id,actor_role,actor_organization_id,organization_id,reason_code,payload->>'packageId',version_references from domain_events where event_type='approved' and aggregate_id=%s order by id desc limit 1",(successor,)).fetchone()
        v1_snapshots_after=connection.execute("select id,material_revision,stage,payload,snapshot_hash from invoice_snapshots where invoice_version_id=%s order by material_revision,stage",(invoice["id"],)).fetchall()
        v2_snapshot_stages={row[0] for row in connection.execute("select stage from invoice_snapshots where invoice_version_id=%s",(successor,)).fetchall()}
        description_chain=connection.execute("""select id,invoice_version_id,correction_actor_id,predecessor_lineage_id
            from field_lineage where field_name='EXP-004.description'
              and invoice_version_id in (%s,%s) order by id""",(invoice["id"],successor)).fetchall()
    assert v1_hashes==submission["packageHashes"] and link==(invoice["id"],successor,returned["id"])
    assert len(reproduction_hashes)==2 and len({row[1] for row in reproduction_hashes})==2 and len({row[2] for row in reproduction_hashes})==2
    assert v1_feedback==("EVIDENCE_CORRECTION","Correct the service evidence and resubmit",["EXP-004"]) and final=="approved"
    assert approval_event[:6]==(government.user_id,Role.GOVERNMENT_REVIEWER.value,"org-government","org-ngo","APPROVED_AS_CORRECTED",v2_package["id"])
    assert {reference["kind"] for reference in approval_event[6]}=={"invoice","submission","package","decision"}
    assert v1_snapshots_after==v1_snapshots_before
    assert v2_snapshot_stages=={"validation","attestation","package","submission"}
    assert len(description_chain)==3
    assert description_chain[1][1]==successor and description_chain[1][3]==description_chain[0][0]
    assert description_chain[2][1]==successor and description_chain[2][2]==PREPARER.user_id
    assert description_chain[2][3]==description_chain[1][0]
    auditor_final=audit_query(AUDITOR,CONTRACT,submitted=True)
    assert {"supports","derived_from","maps_to","validated_by","submitted_as","returned_as","amends","approved_as"} <= {
        item["relationType"] for item in auditor_final["relations"]
    }
    assert all(item["actorId"] and item["actorRole"] and item["actorOrganizationId"] for item in auditor_final["relations"])
    for relation in auditor_final["relations"]:
        relation_document={
            "id":relation["id"],
            "relationType":relation["relationType"],
            "source":relation["source"],
            "target":relation["target"],
            "actor":{"userId":relation["actorId"],"organizationId":relation["actorOrganizationId"],"role":relation["actorRole"]},
            "reasonCode":relation["reasonCode"],
        }
        assert relation["relationHash"]==canonical_hash(relation_document)
    derived=[item for item in auditor_final["relations"] if item["relationType"]=="derived_from"]
    assert derived and all(item["source"]["kind"]=="package" and item["target"]["kind"]=="invoice_snapshot" for item in derived)
    amendment=next(item for item in auditor_final["relations"] if item["relationType"]=="amends")
    assert amendment["source"]["id"]==successor and amendment["target"]["id"]==invoice["id"]
    snapshots_by_id={item["id"]:item for item in auditor_final["snapshots"]}
    for event_item in auditor_final["events"]:
        for reference in event_item["versionReferences"]:
            if reference["kind"]=="invoice_snapshot":
                assert reference["version"]==snapshots_by_id[reference["id"]]["materialRevision"]
    correction_event=next(item for item in auditor_final["events"] if item["eventType"]=="invoice_line_corrected" and item["aggregateId"]==successor and item["payload"].get("correctionId")==correction["id"])
    invoice_reference=next(item for item in correction_event["versionReferences"] if item["kind"]=="invoice")
    assert invoice_reference["version"]==v2["version"]
    assert correction_event["payload"]["materialRevision"]==2
    assert {invoice["id"],successor} <= {item["invoiceVersionId"] for item in auditor_final["snapshots"]}
    reproduced_packages={item["packageId"]:item for item in auditor_final["reproducibility"]}
    assert {submission["packageId"],v2_package["id"]} <= set(reproduced_packages)
    assert all(item["validationInputManifestHash"] and item["buildInputHash"] and item["packageManifestHash"] and item["archiveSha256"] for item in reproduced_packages.values())
    assert all(item["templateId"]=="reimbursement-invoice-pdf" and item["templateVersion"]==1 and len(item["templateHash"])==64 for item in reproduced_packages.values())
    with pytest.raises(psycopg.errors.RaiseException,match="append-only"):
        with database() as connection:
            connection.execute("update invoice_snapshots set payload='{}' where id=%s",(v1_snapshots_before[0][0],))
