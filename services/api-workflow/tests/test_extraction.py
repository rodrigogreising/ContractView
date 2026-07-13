from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from app.artifacts import download_artifact
from app.authorization import Actor, ForbiddenError, Role
from app.document_profiles import confirm_cluster, list_cluster_suggestions
from app.extraction import OcrResponse
from app.ingestion import claim_next_job, create_upload_job, list_jobs, process_job
from app.runtime import database
from configuration_helpers import ensure_active_configuration

CONTRACT = "contract-synthetic-agency-ngo-2026"
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
FILES = Path("/app/fixtures/files")


@pytest.fixture(scope="module", autouse=True)
def active_profile_configuration():
    return ensure_active_configuration(ADMIN, CONTRACT)

VALID_TEXT = """Synthetic Program Supplies Vendor B
Test fixture only - no real organization, person, account, or transaction.
Invoice: SYN-SUP-0618
Date: 2026-06-18
VENDOR INVOICE
Description: Workshop materials and learning kits
Amount: $1,820.00
Printed subtotal: $1,820.00
Approved adjustment: $-540.00
Approved claim total: $1,280.00
APPROVAL NOTE
Claim only the approved adjusted total; exclude the non-program materials adjustment.
Expense reference: VENDOR-INVOICE-EXP-003
"""


class FakeAdapter:
    provider = "fixture-provider"
    model = "fixture-model-v1"
    def __init__(self, response=None, error=None): self.response, self.error = response, error
    def extract(self, filename, media_type, content):
        if self.error: raise self.error
        return self.response


def run_job(filename, content, adapter=None):
    job = create_upload_job(PREPARER, CONTRACT, filename, "application/pdf", content)
    claimed = claim_next_job(); assert claimed and claimed.id == job.id
    process_job(claimed, adapter)
    return job, {item.id:item for item in list_jobs(PREPARER, CONTRACT)}[job.id]


def test_real_tesseract_worker_adapter_extracts_golden_draft_and_full_trace():
    job, completed = run_job("golden-exp-003.pdf", (FILES / "vendor-invoice-exp-003.pdf").read_bytes())
    assert completed.status == "completed"
    with database() as connection:
        run = connection.execute(
            """select id,raw_response_artifact_id,provider,model,prompt_version,parser_version,schema_version,
                      source_location,confidence,status,routing_reason from extraction_runs where job_id=%s""", (job.id,)
        ).fetchone()
        fields = dict(connection.execute(
            "select field_name,proposed_value from extraction_fields where extraction_run_id=%s", (run[0],)
        ).fetchall())
        event = connection.execute(
            "select event_type,payload->>'rawResponseArtifactId' from domain_events where aggregate_id=%s", (run[0],)
        ).fetchone()
    assert fields == {"vendor":"Synthetic Program Supplies Vendor B","date":"2026-06-18","amount":"1820.00","sourceReference":"VENDOR-INVOICE-EXP-003"}
    assert run[2:7] == ("tesseract-cli","tesseract-5.5.0-eng+spa","not-applicable-deterministic-profile-v1","deterministic-document-profile-parser-v1","document-intake-result-v1")
    assert run[7] == "page=1" and run[8] > Decimal("0.8500")
    assert run[9:] == ("needs_review", "recognized_profile_draft")
    assert event[1] == run[1]
    with database() as connection:
        route = connection.execute(
            """select m.outcome,m.match_kind,v.profile_key,f.specification_version,
                      m.ledger_match_outcome,m.result_hash
                 from document_profile_match_results m
                 join document_profile_versions v on v.id=m.profile_version_id
                 join document_fingerprints f on f.id=m.fingerprint_id
                where m.extraction_run_id=%s""",
            (run[0],),
        ).fetchone()
        locations = dict(connection.execute(
            "select field_name,source_location from extraction_fields where extraction_run_id=%s",
            (run[0],),
        ).fetchall())
    assert route[0:4] == ("recognized_profile_draft", "exact", "vendor_invoice_en", "document-layout-signals-v1")
    assert route[4] in {"matched", "unmatched"} and len(route[5]) == 64
    assert locations == {
        "vendor": "page=1;line=1;label=vendor_alias",
        "date": "page=1;line=6;label=date",
        "amount": "page=1;line=12;label=amount",
        "sourceReference": "page=1;line=23;label=expense reference",
    }
    assert b"Workshop materials" in download_artifact(PREPARER, run[1])
    with pytest.raises(ForbiddenError):
        download_artifact(AUDITOR, run[1])


def test_real_spanish_tesseract_fixture_uses_exact_spanish_profile_and_sources():
    job, completed = run_job(
        "golden-es-001.pdf",
        (FILES / "synthetic-vendor-invoice-es-001.pdf").read_bytes(),
    )
    assert completed.status == "completed"
    with database() as connection:
        row = connection.execute(
            """select m.outcome,v.profile_key,f.language_tag,m.result_hash
                 from extraction_runs r
                 join document_profile_match_results m on m.extraction_run_id=r.id
                 join document_profile_versions v on v.id=m.profile_version_id
                 join document_fingerprints f on f.extraction_run_id=r.id
                where r.job_id=%s""",
            (job.id,),
        ).fetchone()
        fields = dict(connection.execute(
            """select x.field_name,x.proposed_value from extraction_fields x
                 join extraction_runs r on r.id=x.extraction_run_id where r.job_id=%s""",
            (job.id,),
        ).fetchall())
        locations = dict(connection.execute(
            """select x.field_name,x.source_location from extraction_fields x
                 join extraction_runs r on r.id=x.extraction_run_id where r.job_id=%s""",
            (job.id,),
        ).fetchall())
    assert row[0:3] == ("recognized_profile_draft", "vendor_invoice_es", "es")
    assert len(row[3]) == 64
    assert fields == {
        "vendor": "Synthetic Materiales Comunitarios A",
        "date": "2026-06-20",
        "amount": "740.00",
        "sourceReference": "EXP-ES-001",
    }
    assert set(locations) == set(fields)
    assert all(value.startswith("page=1;line=") for value in locations.values())


def test_low_confidence_routes_to_review_without_creating_truth():
    response = OcrResponse("fixture-provider","fixture-model-v1",VALID_TEXT,Decimal("0.4200"))
    job, completed = run_job("low-confidence.pdf", b"synthetic-low-confidence", FakeAdapter(response=response))
    assert completed.status == "completed"
    with database() as connection:
        run = connection.execute("select status,routing_reason from extraction_runs where job_id=%s", (job.id,)).fetchone()
        statuses = connection.execute("select distinct review_status from extraction_fields where extraction_run_id=(select id from extraction_runs where job_id=%s)", (job.id,)).fetchall()
    assert run == ("needs_review", "LOW_CONFIDENCE")
    assert statuses == [("proposed",)]


def test_identical_declared_inputs_reproduce_fingerprint_result_and_normalized_fields():
    records = []
    for filename in ("replay-one.pdf", "replay-two.pdf"):
        job, completed = run_job(
            filename,
            b"same-synthetic-artifact-bytes",
            FakeAdapter(response=OcrResponse("fixture-provider", "fixture-model-v1", VALID_TEXT, Decimal("0.9900"))),
        )
        assert completed.status == "completed"
        with database() as connection:
            record = connection.execute(
                """select f.fingerprint_sha256,m.result_hash,
                          jsonb_object_agg(x.field_name,x.proposed_value order by x.field_name)
                     from extraction_runs r
                     join document_fingerprints f on f.extraction_run_id=r.id
                     join document_profile_match_results m on m.extraction_run_id=r.id
                     join extraction_fields x on x.extraction_run_id=r.id
                    where r.job_id=%s group by f.id,m.id""",
                (job.id,),
            ).fetchone()
        records.append(record)
    assert records[0] == records[1]


def test_runtime_fingerprint_and_match_evidence_cannot_be_rewritten():
    job, completed = run_job(
        "immutable-route-evidence.pdf",
        b"immutable-synthetic-route-evidence",
        FakeAdapter(
            response=OcrResponse(
                "fixture-provider", "fixture-model-v1", VALID_TEXT, Decimal("0.9900")
            )
        ),
    )
    assert completed.status == "completed"
    with database() as connection:
        references = connection.execute(
            """select f.id,m.id,m.profile_version_id,m.configuration_version_id
                 from extraction_runs r
                 join document_fingerprints f on f.extraction_run_id=r.id
                 join document_profile_match_results m on m.extraction_run_id=r.id
                where r.job_id=%s""",
            (job.id,),
        ).fetchone()
    assert all(references)
    for table, identifier in (
        ("document_fingerprints", references[0]),
        ("document_profile_match_results", references[1]),
    ):
        with database() as connection:
            with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
                connection.execute(
                    f"update {table} set created_at=now() where id=%s", (identifier,)
                )


def test_provider_failure_is_explicit_and_has_no_fields():
    job, failed = run_job("provider-failure.pdf", b"provider-failure", FakeAdapter(error=RuntimeError("provider unavailable")))
    assert failed.status == "failed" and failed.error_code == "PROCESSING_FAILED" and failed.error_message
    with database() as connection:
        run = connection.execute("select status,routing_reason,error_message from extraction_runs where job_id=%s", (job.id,)).fetchone()
        fields = connection.execute("select count(*) from extraction_fields where extraction_run_id=(select id from extraction_runs where job_id=%s)", (job.id,)).fetchone()[0]
    assert run[0:2] == ("failed", "PROVIDER_OR_RESPONSE_FAILURE") and run[2]
    assert fields == 0


@pytest.mark.parametrize(("fixture_name", "text"), [
    ("changed-layout.pdf", "Synthetic Workshop Goods A\nTest fixture only - no real organization, person, account, or transaction.\nInvoice: SYN-CHANGED-0625\nUNDECLARED LAYOUT ROW 1\nUNDECLARED LAYOUT ROW 2\nUNDECLARED LAYOUT ROW 3\nDate: 2026-06-25\nVENDOR INVOICE\nDescription: Shifted deterministic layout\nAmount: $325.00\nPrinted subtotal: $325.00\nApproved claim total: $325.00\nAPPROVAL NOTE\nThe labels remain valid but their layout positions changed.\nExpense reference: EXP-CHANGED-001\n"),
    ("unknown-layout.pdf", "SYNTHETIC SUPPORTING DOCUMENT\nReference table for deterministic review routing.\nEntry A 2026-06-27 USD 111.00\n"),
])
def test_changed_and_unknown_layouts_route_safely_without_canonical_mutation(fixture_name, text):
    with database() as connection:
        before = (
            connection.execute("select count(*) from invoice_versions").fetchone()[0],
            connection.execute("select count(*) from validation_runs").fetchone()[0],
            connection.execute("select count(*) from document_profile_active_assignments").fetchone()[0],
        )
    job, completed = run_job(
        fixture_name,
        text.encode(),
        FakeAdapter(response=OcrResponse("fixture-provider", "fixture-model-v1", text, Decimal("0.9900"))),
    )
    assert completed.status == "completed"
    with database() as connection:
        evidence = connection.execute(
            """select m.outcome,m.match_kind,m.profile_version_id,m.configuration_version_id,
                      m.ledger_match_outcome,c.id,c.canonical,count(x.id)
                 from document_profile_match_results m
                 join document_fingerprints f on f.id=m.fingerprint_id
                 join document_cluster_projections c on c.fingerprint_id=f.id
                 left join extraction_fields x on x.extraction_run_id=m.extraction_run_id
                where m.extraction_run_id=(select id from extraction_runs where job_id=%s)
                group by m.id,c.id""",
            (job.id,),
        ).fetchone()
        after = (
            connection.execute("select count(*) from invoice_versions").fetchone()[0],
            connection.execute("select count(*) from validation_runs").fetchone()[0],
            connection.execute("select count(*) from document_profile_active_assignments").fetchone()[0],
        )
    assert evidence[0:3] == ("needs_profile_review", "none", None)
    assert evidence[3] is not None
    assert evidence[4] == "not_evaluated"
    assert evidence[5] and evidence[6:] == (False, 0)
    assert after == before


def test_cluster_confirmation_is_admin_only_and_creates_only_a_draft_association():
    text = "SYNTHETIC UNKNOWN FORMAT\nVendor: Synthetic Workshop Goods A\nTotal amount: USD 25.00\n"
    run_job(
        "cluster-confirmation.pdf",
        text.encode(),
        FakeAdapter(response=OcrResponse("fixture-provider", "fixture-model-v1", text, Decimal("0.9900"))),
    )
    cluster = list_cluster_suggestions(
        Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR), CONTRACT
    )[-1]
    with database() as connection:
        before = (
            connection.execute("select count(*) from document_profile_cluster_associations").fetchone()[0],
            connection.execute("select count(*) from document_profile_active_assignments").fetchone()[0],
        )
    with pytest.raises(ForbiddenError):
        confirm_cluster(PREPARER, cluster["id"], "vendor_invoice_candidate", "Unauthorized confirmation")
    with database() as connection:
        denied = (
            connection.execute("select count(*) from document_profile_cluster_associations").fetchone()[0],
            connection.execute("select count(*) from document_profile_active_assignments").fetchone()[0],
        )
    assert denied == before
    association = confirm_cluster(
        Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR),
        cluster["id"],
        "vendor_invoice_candidate",
        "Confirm suggestion as a draft association only",
    )
    assert association["status"] == "draft"
    with database() as connection:
        after = (
            connection.execute("select count(*) from document_profile_cluster_associations").fetchone()[0],
            connection.execute("select count(*) from document_profile_active_assignments").fetchone()[0],
        )
    assert after == (before[0] + 1, before[1])
