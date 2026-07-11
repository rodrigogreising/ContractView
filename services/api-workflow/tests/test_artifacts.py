import psycopg
import pytest

from app.artifacts import download_artifact, store_artifact
from app.authorization import Actor, ForbiddenError, Role
from app.runtime import database, object_store
from app.settings import get_settings

PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
OTHER_NGO = Actor("outside-user", "org-outside", Role.NGO_PREPARER)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
CONTRACT = "contract-metro-harbor-2026"


def test_original_and_generated_bytes_are_stored_with_integrity_metadata():
    original = store_artifact(PREPARER, CONTRACT, "ledger.csv", "text/csv", b"date,amount\n2026-01-01,10.00\n")
    generated = store_artifact(PREPARER, CONTRACT, "invoice.pdf", "application/pdf", b"%PDF synthetic", artifact_kind="generated")
    assert download_artifact(PREPARER, original.id).startswith(b"date,amount")
    with pytest.raises(ForbiddenError):
        download_artifact(AUDITOR, generated.id)
    with database() as connection:
        connection.execute("update artifacts set submitted=true where id=%s", (generated.id,))
        connection.commit()
    assert download_artifact(AUDITOR, generated.id) == b"%PDF synthetic"
    with database() as connection:
        row = connection.execute(
            "select sha256, byte_size, media_type, created_by, organization_id, created_at is not null from artifacts where id=%s",
            (original.id,),
        ).fetchone()
    assert row[0] == original.sha256
    assert row[1:] == (len(b"date,amount\n2026-01-01,10.00\n"), "text/csv", PREPARER.user_id, "org-ngo", True)


def test_replacement_creates_new_bytes_and_immutable_relation():
    first = store_artifact(PREPARER, CONTRACT, "receipt.png", "image/png", b"first")
    second = store_artifact(PREPARER, CONTRACT, "receipt.png", "image/png", b"corrected", predecessor_id=first.id)
    assert first.id != second.id and first.object_key != second.object_key and first.sha256 != second.sha256
    assert download_artifact(PREPARER, first.id) == b"first"
    assert download_artifact(PREPARER, second.id) == b"corrected"
    with database() as connection:
        relation = connection.execute(
            "select relation_type from artifact_relations where predecessor_artifact_id=%s and successor_artifact_id=%s",
            (first.id, second.id),
        ).fetchone()[0]
    assert relation == "replaces"
    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        with database() as connection:
            connection.execute("delete from artifacts where id=%s", (first.id,))


def test_cross_organization_download_is_denied_before_object_read(monkeypatch):
    artifact = store_artifact(PREPARER, CONTRACT, "private.csv", "text/csv", b"private")
    touched = False
    def forbidden_object_store():
        nonlocal touched
        touched = True
        return object_store()
    monkeypatch.setattr("app.artifacts.object_store", forbidden_object_store)
    with pytest.raises(ForbiddenError):
        download_artifact(OTHER_NGO, artifact.id)
    assert touched is False


def test_database_reference_matches_minio_object_and_hash():
    artifact = store_artifact(PREPARER, CONTRACT, "manifest.json", "application/json", b'{"version":1}', artifact_kind="generated")
    stat = object_store().stat_object(get_settings().minio_bucket, artifact.object_key)
    assert stat.size == artifact.byte_size
    assert download_artifact(PREPARER, artifact.id) == b'{"version":1}'
