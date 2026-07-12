from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import uuid

from .artifacts import get_artifact, read_and_verify_artifact, store_artifact
from .access_scope import contract_scope, job_scope
from ...authorization import Action, Actor, ResourceKind, execute_authorized, require_permission

from ..ports.statements import Statement
from ..transaction import transaction as database
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED = {
    ".csv": ("text/csv", "ledger_import"),
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "ledger_import"),
    ".pdf": ("application/pdf", "evidence_extract"),
    ".png": ("image/png", "evidence_extract"),
    ".jpg": ("image/jpeg", "evidence_extract"),
    ".jpeg": ("image/jpeg", "evidence_extract"),
}


class InvalidUpload(ValueError):
    pass


@dataclass(frozen=True)
class IngestionJob:
    id: str
    artifact_id: str
    contract_id: str
    organization_id: str
    job_type: str
    status: str
    attempt_count: int
    error_code: str | None
    error_message: str | None


def _job_from_row(row) -> IngestionJob:
    return IngestionJob(*row)


def create_upload_job(actor: Actor, contract_id: str, filename: str, media_type: str, content: bytes) -> IngestionJob:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise InvalidUpload("Use CSV, XLSX, PDF, PNG, or JPEG files")
    expected_media, job_type = ALLOWED[suffix]
    if media_type != expected_media and not (suffix == ".csv" and media_type in {"text/csv", "application/vnd.ms-excel"}):
        raise InvalidUpload(f"{filename} content type does not match its extension")
    if not content:
        raise InvalidUpload("The selected file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise InvalidUpload("File exceeds the 10 MB POC limit")

    def command() -> IngestionJob:
        digest = sha256(content).hexdigest()
        with database() as connection:
            existing = connection.read_models.execute(Statement.INGESTION_READ_ARTIFACTS_INGESTION_JOBS_001,
                (contract_id, actor.organization_id, digest, filename, job_type),
            ).fetchone()
        if existing:
            return _job_from_row(existing)
        artifact = store_artifact(actor, contract_id, filename, expected_media, content)
        job_id = f"job-{uuid.uuid4().hex}"
        with database() as connection:
            row = connection.extraction.execute(Statement.INGESTION_WRITE_INGESTION_JOBS_002,
                (job_id, artifact.id, contract_id, actor.organization_id, job_type, actor.user_id),
            ).fetchone()
            connection.commit()
        return _job_from_row(row)
    scope = contract_scope(actor, contract_id, f"job:{contract_id}", ResourceKind.JOB)
    return execute_authorized(actor, Action.CREATE, scope, command)


def list_jobs(actor: Actor, contract_id: str) -> list[IngestionJob]:
    require_permission(
        actor,
        Action.READ,
        contract_scope(actor, contract_id, f"jobs:{contract_id}", ResourceKind.JOB),
    )
    with database() as connection:
        rows = connection.extraction.execute(Statement.INGESTION_READ_INGESTION_JOBS_003, (contract_id,)
        ).fetchall()
    jobs = [_job_from_row(row) for row in rows]
    for job in jobs:
        require_permission(actor, Action.READ, job_scope(actor, job.id))
    return jobs


def claim_next_job() -> IngestionJob | None:
    with database() as connection:
        row = connection.extraction.execute(Statement.INGESTION_WRITE_INGESTION_JOBS_004
        ).fetchone()
        connection.commit()
    return _job_from_row(row) if row else None


def process_job(job: IngestionJob, extraction_adapter=None) -> None:
    try:
        artifact = get_artifact(job.artifact_id)
        if not artifact:
            raise RuntimeError("Registered artifact is missing")
        if job.job_type == "ledger_import":
            from .ledger_import import import_ledger
            import_ledger(job, artifact)
        else:
            from .extraction import extract_evidence
            extract_evidence(job, artifact, extraction_adapter)
        with database() as connection:
            connection.extraction.execute(Statement.INGESTION_WRITE_INGESTION_JOBS_005,
                (job.id,),
            )
            connection.commit()
    except Exception as error:
        with database() as connection:
            connection.extraction.execute(Statement.INGESTION_WRITE_INGESTION_JOBS_006,
                (str(error), job.id),
            )
            connection.commit()


def process_next_job() -> bool:
    job = claim_next_job()
    if not job:
        return False
    process_job(job)
    return True
