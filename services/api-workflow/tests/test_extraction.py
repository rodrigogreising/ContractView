from decimal import Decimal
from pathlib import Path

import pytest

from app.artifacts import download_artifact
from app.authorization import Actor, ForbiddenError, Role
from app.extraction import OcrResponse
from app.ingestion import claim_next_job, create_upload_job, list_jobs, process_job
from app.runtime import database

CONTRACT = "contract-synthetic-agency-ngo-2026"
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
FILES = Path("/app/fixtures/files")

VALID_TEXT = """Synthetic Program Supplies Vendor B
Date: 2026-06-18
Workshop materials and learning kits $1,820.00
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
    assert run[2:7] == ("tesseract-cli","tesseract-5.5.0-eng","vendor-invoice-fields-v1","vendor-invoice-parser-v1","vendor-date-amount-reference-v1")
    assert run[7] == "page=1" and run[8] > Decimal("0.8500")
    assert run[9:] == ("needs_review", "HUMAN_REVIEW_REQUIRED")
    assert event == ("extraction_drafted", run[1])
    assert b"Workshop materials" in download_artifact(PREPARER, run[1])
    with pytest.raises(ForbiddenError):
        download_artifact(AUDITOR, run[1])


def test_low_confidence_routes_to_review_without_creating_truth():
    response = OcrResponse("fixture-provider","fixture-model-v1",VALID_TEXT,Decimal("0.4200"))
    job, completed = run_job("low-confidence.pdf", b"synthetic-low-confidence", FakeAdapter(response=response))
    assert completed.status == "completed"
    with database() as connection:
        run = connection.execute("select status,routing_reason from extraction_runs where job_id=%s", (job.id,)).fetchone()
        statuses = connection.execute("select distinct review_status from extraction_fields where extraction_run_id=(select id from extraction_runs where job_id=%s)", (job.id,)).fetchall()
    assert run == ("needs_review", "LOW_CONFIDENCE")
    assert statuses == [("proposed",)]


def test_provider_and_invalid_response_fail_visibly_without_fields():
    cases = [
        ("provider-failure.pdf", FakeAdapter(error=RuntimeError("provider unavailable"))),
        ("invalid-response.pdf", FakeAdapter(response=OcrResponse("fixture-provider","fixture-model-v1","nonsense",Decimal("0.9900")))),
    ]
    for filename, adapter in cases:
        job, failed = run_job(filename, filename.encode(), adapter)
        assert failed.status == "failed" and failed.error_code == "PROCESSING_FAILED" and failed.error_message
        with database() as connection:
            run = connection.execute("select status,routing_reason,error_message from extraction_runs where job_id=%s", (job.id,)).fetchone()
            fields = connection.execute("select count(*) from extraction_fields where extraction_run_id=(select id from extraction_runs where job_id=%s)", (job.id,)).fetchone()[0]
        assert run[0:2] == ("failed", "PROVIDER_OR_RESPONSE_FAILURE") and run[2]
        assert fields == 0
