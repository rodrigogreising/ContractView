from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import uuid

from .access_scope import artifact_scope, contract_scope
from .authorization import Action, Actor, ResourceKind, Role, execute_authorized, require_permission
from .runtime import database, object_store
from .settings import get_settings
from .provenance import append_event_tx


class ArtifactIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class Artifact:
    id: str
    contract_id: str
    organization_id: str
    agency_organization_id: str
    object_key: str
    filename: str
    media_type: str
    byte_size: int
    sha256: str
    artifact_kind: str
    created_by: str
    submitted: bool


def store_artifact(
    actor: Actor,
    contract_id: str,
    filename: str,
    media_type: str,
    content: bytes,
    *,
    artifact_kind: str = "original",
    predecessor_id: str | None = None,
    relation_type: str | None = None,
) -> Artifact:
    artifact_id = f"artifact-{uuid.uuid4().hex}"

    def command() -> Artifact:
        digest = sha256(content).hexdigest()
        object_key = f"{actor.organization_id}/{artifact_id}/{digest}"
        with database() as connection:
            contract = connection.execute(
                "select agency_organization_id, ngo_organization_id from contracts where id=%s", (contract_id,)
            ).fetchone()
            if not contract or contract[1] != actor.organization_id:
                raise ValueError("Contract does not belong to actor organization")
            if predecessor_id:
                predecessor = connection.execute(
                    "select organization_id, artifact_kind from artifacts where id=%s", (predecessor_id,)
                ).fetchone()
                if not predecessor or predecessor[0] != actor.organization_id:
                    raise ValueError("Predecessor is not in actor organization")
            client = object_store()
            client.put_object(
                get_settings().minio_bucket,
                object_key,
                BytesIO(content),
                len(content),
                content_type=media_type,
            )
            try:
                connection.execute(
                    """insert into artifacts
                       (id, contract_id, organization_id, agency_organization_id, object_key,
                        filename, media_type, byte_size, sha256, artifact_kind, created_by)
                       values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (artifact_id, contract_id, actor.organization_id, contract[0], object_key,
                     filename, media_type, len(content), digest, artifact_kind, actor.user_id),
                )
                if predecessor_id:
                    relation = relation_type or ("regenerates" if artifact_kind == "generated" else "replaces")
                    connection.execute(
                        "insert into artifact_relations(predecessor_artifact_id, successor_artifact_id, relation_type) values (%s,%s,%s)",
                        (predecessor_id, artifact_id, relation),
                    )
                append_event_tx(connection, "artifact_uploaded", "artifact", artifact_id,
                                actor_id=actor.user_id, organization_id=actor.organization_id,
                                contract_id=contract_id,
                                payload={"sha256": digest, "byteSize": len(content), "mediaType": media_type,
                                         "kind": artifact_kind, "predecessorId": predecessor_id})
                connection.commit()
            except Exception:
                client.remove_object(get_settings().minio_bucket, object_key)
                raise
        return Artifact(artifact_id, contract_id, actor.organization_id, contract[0], object_key,
                        filename, media_type, len(content), digest, artifact_kind, actor.user_id, False)

    if artifact_kind == "generated" and actor.role is Role.NGO_APPROVER:
        package_scope = contract_scope(actor, contract_id, artifact_id, ResourceKind.PACKAGE)
        return execute_authorized(actor, Action.SUBMIT, package_scope, command)
    scope = contract_scope(actor, contract_id, artifact_id, ResourceKind.ARTIFACT)
    return execute_authorized(actor, Action.CREATE, scope, command)


def get_artifact(artifact_id: str) -> Artifact | None:
    with database() as connection:
        row = connection.execute(
            """select id, contract_id, organization_id, agency_organization_id, object_key,
                      filename, media_type, byte_size, sha256, artifact_kind, created_by, submitted
               from artifacts where id=%s""", (artifact_id,)
        ).fetchone()
    return Artifact(*row) if row else None


def download_artifact(actor: Actor, artifact_id: str) -> bytes:
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise FileNotFoundError(artifact_id)
    require_permission(actor, Action.READ, artifact_scope(actor, artifact_id))
    return read_and_verify_artifact(artifact)


def read_and_verify_artifact(artifact: Artifact) -> bytes:
    response = object_store().get_object(get_settings().minio_bucket, artifact.object_key)
    try:
        content = response.read()
    finally:
        response.close()
        response.release_conn()
    if len(content) != artifact.byte_size or sha256(content).hexdigest() != artifact.sha256:
        raise ArtifactIntegrityError(f"Artifact {artifact.id} failed integrity verification")
    return content
