from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import uuid

from .artifacts import get_artifact, read_and_verify_artifact, store_artifact
from .access_scope import contract_scope, job_scope
from .authorization import Action, Actor, ResourceKind, execute_authorized, require_permission
from .runtime import database

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
            existing = connection.execute(
                """select j.id,j.artifact_id,j.contract_id,j.organization_id,j.job_type,j.status,
                          j.attempt_count,j.error_code,j.error_message
                   from ingestion_jobs j join artifacts a on a.id=j.artifact_id
                   where j.contract_id=%s and j.organization_id=%s and a.sha256=%s and a.filename=%s and j.job_type=%s""",
                (contract_id, actor.organization_id, digest, filename, job_type),
            ).fetchone()
        if existing:
            return _job_from_row(existing)
        artifact = store_artifact(actor, contract_id, filename, expected_media, content)
        job_id = f"job-{uuid.uuid4().hex}"
        with database() as connection:
            row = connection.execute(
                """insert into ingestion_jobs(id,artifact_id,contract_id,organization_id,job_type,status,created_by)
                   values (%s,%s,%s,%s,%s,'queued',%s)
                   returning id,artifact_id,contract_id,organization_id,job_type,status,attempt_count,error_code,error_message""",
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
        rows = connection.execute(
            """select id,artifact_id,contract_id,organization_id,job_type,status,attempt_count,error_code,error_message
               from ingestion_jobs where contract_id=%s order by created_at""", (contract_id,)
        ).fetchall()
    jobs = [_job_from_row(row) for row in rows]
    for job in jobs:
        require_permission(actor, Action.READ, job_scope(actor, job.id))
    return jobs


def claim_next_job() -> IngestionJob | None:
    with database() as connection:
        row = connection.execute(
            """with next as (
                 select id from ingestion_jobs where status='queued' order by created_at for update skip locked limit 1
               ) update ingestion_jobs j set status='running', started_at=now(), attempt_count=attempt_count+1
               from next where j.id=next.id
               returning j.id,j.artifact_id,j.contract_id,j.organization_id,j.job_type,j.status,
                         j.attempt_count,j.error_code,j.error_message"""
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
            connection.execute(
                "update ingestion_jobs set status='completed', completed_at=now(), error_code=null, error_message=null where id=%s and status='running'",
                (job.id,),
            )
            connection.commit()
    except Exception as error:
        with database() as connection:
            connection.execute(
                "update ingestion_jobs set status='failed', completed_at=now(), error_code='PROCESSING_FAILED', error_message=%s where id=%s and status='running'",
                (str(error), job.id),
            )
            connection.commit()


def process_next_job() -> bool:
    job = claim_next_job()
    if not job:
        return False
    process_job(job)
    return True
