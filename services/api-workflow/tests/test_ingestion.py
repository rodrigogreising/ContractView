import pytest
from pathlib import Path

from app.artifacts import get_artifact
from app.authorization import Actor, ForbiddenError, Role
from app.ingestion import (
    MAX_UPLOAD_BYTES, InvalidUpload, claim_next_job, create_upload_job, list_jobs, process_job,
)
from app.runtime import database, object_store
from app.settings import get_settings
from configuration_helpers import ensure_active_configuration as ensure_active_configuration_for_contract

CONTRACT = "contract-synthetic-agency-ngo-2026"
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
APPROVER = Actor("user-ngo-approver", "org-ngo", Role.NGO_APPROVER)
OTHER_NGO = Actor("outside-user", "org-outside", Role.NGO_PREPARER)
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
FIXTURES = Path("/app/fixtures/files")

def ensure_active_configuration():
    return ensure_active_configuration_for_contract(ADMIN, CONTRACT)


@pytest.mark.parametrize(("filename", "media_type", "job_type", "terminal_status"), [
    ("ledger.csv", "text/csv", "ledger_import", "completed"),
    ("ledger.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "ledger_import", "completed"),
    ("invoice.pdf", "application/pdf", "evidence_extract", "completed"),
    ("receipt.png", "image/png", "evidence_extract", "failed"),
    ("receipt.jpg", "image/jpeg", "evidence_extract", "failed"),
])
def test_allowed_uploads_queue_run_and_reach_visible_terminal_status(filename, media_type, job_type, terminal_status):
    ensure_active_configuration()
    if filename.endswith(".csv"):
        content = (FIXTURES / "ledger-june-2026.csv").read_bytes()
    elif filename.endswith(".xlsx"):
        content = (FIXTURES / "ledger-june-2026.xlsx").read_bytes()
    elif filename.endswith(".pdf"):
        content = (FIXTURES / "vendor-invoice-exp-003.pdf").read_bytes()
    elif filename.endswith(".png"):
        content = (FIXTURES / "vendor-invoice-exp-004.png").read_bytes()
    else:
        content = b"not-a-supported-vendor-invoice"
    job = create_upload_job(PREPARER, CONTRACT, filename, media_type, content)
    assert job.status == "queued" and job.job_type == job_type
    claimed = claim_next_job()
    assert claimed is not None and claimed.status == "running" and claimed.attempt_count == 1
    process_job(claimed)
    completed = {item.id: item for item in list_jobs(PREPARER, CONTRACT)}[claimed.id]
    assert completed.status == terminal_status
    if terminal_status == "failed": assert completed.error_message


@pytest.mark.parametrize(("filename", "media_type", "content", "message"), [
    ("malware.exe", "application/octet-stream", b"x", "Use CSV"),
    ("ledger.csv", "application/pdf", b"x", "does not match"),
    ("empty.pdf", "application/pdf", b"", "empty"),
    ("huge.pdf", "application/pdf", b"x" * (MAX_UPLOAD_BYTES + 1), "10 MB"),
])
def test_invalid_uploads_are_actionable_and_create_no_job(filename, media_type, content, message):
    with database() as connection:
        before = connection.execute("select count(*) from ingestion_jobs").fetchone()[0]
    with pytest.raises(InvalidUpload, match=message):
        create_upload_job(PREPARER, CONTRACT, filename, media_type, content)
    with database() as connection:
        after = connection.execute("select count(*) from ingestion_jobs").fetchone()[0]
    assert after == before


def test_identical_retry_is_idempotent():
    ensure_active_configuration()
    content = (FIXTURES / "ledger-june-2026.csv").read_bytes()
    first = create_upload_job(PREPARER, CONTRACT, "retry-ledger.csv", "text/csv", content)
    second = create_upload_job(PREPARER, CONTRACT, "retry-ledger.csv", "text/csv", content)
    assert second.id == first.id and second.artifact_id == first.artifact_id
    with database() as connection:
        count = connection.execute("select count(*) from ingestion_jobs where id=%s", (first.id,)).fetchone()[0]
    assert count == 1
    claimed = claim_next_job()
    assert claimed is not None and claimed.id == first.id
    process_job(claimed)


def test_failed_worker_job_has_visible_actionable_error():
    job = create_upload_job(PREPARER, CONTRACT, "missing-object.pdf", "application/pdf", b"will-disappear")
    artifact = get_artifact(job.artifact_id)
    object_store().remove_object(get_settings().minio_bucket, artifact.object_key)
    claimed = claim_next_job()
    assert claimed is not None
    process_job(claimed)
    failed = {item.id: item for item in list_jobs(PREPARER, CONTRACT)}[claimed.id]
    assert failed.status == "failed"
    assert failed.error_code == "PROCESSING_FAILED"
    assert failed.error_message


def test_only_preparer_creates_and_cross_organization_cannot_list():
    with pytest.raises(ForbiddenError):
        create_upload_job(APPROVER, CONTRACT, "approver.csv", "text/csv", b"no")
    private = create_upload_job(PREPARER, CONTRACT, "private-job.csv", "text/csv", b"private")
    with pytest.raises(ForbiddenError):
        list_jobs(OTHER_NGO, CONTRACT)
    claimed = claim_next_job()
    assert claimed is not None and claimed.id == private.id
    process_job(claimed)
