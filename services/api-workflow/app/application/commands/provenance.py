from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any
import uuid

from .access_scope import audit_scope
from ...authorization import Action, Actor, Role, require_permission
from ...shared_contracts import MATERIAL_EVENT_TYPES, RelationContract, VersionReference

from ..ports.statements import Statement
from ..transaction import transaction as database
EVENT_TYPES = MATERIAL_EVENT_TYPES


@dataclass(frozen=True)
class LineageInput:
    contract_id: str
    organization_id: str
    field_name: str
    field_value: Any
    source_artifact_id: str | None = None
    source_location: str | None = None
    importer_version: str | None = None
    extractor_provider: str | None = None
    extractor_model: str | None = None
    prompt_version: str | None = None
    parser_version: str | None = None
    mapping_version: str | None = None
    correction_actor_id: str | None = None
    correction_reason: str | None = None
    validation_run_id: str | None = None
    invoice_version_id: str | None = None
    package_artifact_id: str | None = None
    predecessor_lineage_id: int | None = None


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _default_reference(aggregate_type: str, aggregate_id: str, payload: dict) -> dict:
    kinds = {
        "artifact": "artifact",
        "configuration_version": "configuration",
        "invoice_version": "invoice",
        "invoice_line": "entity",
        "validation_run": "validation_run",
        "validation_finding": "entity",
        "extraction_run": "entity",
        "extraction_field": "entity",
        "package": "package",
        "session": "entity",
    }
    version = (
        payload.get("invoiceVersion")
        or payload.get("configurationVersion")
        or payload.get("engineVersion")
        or payload.get("attestationVersion")
        or payload.get("version")
        or 1
    )
    return {"kind": kinds.get(aggregate_type, "entity"), "id": aggregate_id, "version": version}


def append_event_tx(
    connection,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    *,
    actor_id: str | None = None,
    actor_role: str | None = None,
    organization_id: str | None = None,
    contract_id: str | None = None,
    payload: dict | None = None,
    reason_code: str | None = None,
    version_references: list[dict] | None = None,
    schema_version: int = 1,
) -> int:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unsupported material event: {event_type}")
    body = payload or {}
    actor_organization_id = None
    if actor_id:
        actor = connection.identity.execute(
            Statement.PROVENANCE_READ_USERS_008,
            (actor_id,),
        ).fetchone()
        if actor:
            actor_role = actor[0]
            actor_organization_id = actor[1]
            organization_id = organization_id or actor_organization_id
    references = version_references or [
        _default_reference(aggregate_type, aggregate_id, body)
    ]
    normalized_references = [
        VersionReference.model_validate(reference).model_dump(by_alias=True)
        for reference in references
    ]
    event_key = f"event-{uuid.uuid4().hex}"
    event_body = {
        "eventId": event_key,
        "eventType": event_type,
        "schemaVersion": schema_version,
        "actorId": actor_id,
        "actorRole": actor_role,
        "actorOrganizationId": actor_organization_id,
        "organizationId": organization_id,
        "contractId": contract_id,
        "aggregateType": aggregate_type,
        "aggregateId": aggregate_id,
        "payload": body,
        "reasonCode": reason_code,
        "versionReferences": normalized_references,
    }
    event_hash = sha256(_canonical(event_body).encode()).hexdigest()
    return connection.provenance.execute(Statement.PROVENANCE_WRITE_DOMAIN_EVENTS_001,
        (
            event_key,
            event_type,
            schema_version,
            actor_id,
            actor_role,
            actor_organization_id,
            organization_id,
            contract_id,
            aggregate_type,
            aggregate_id,
            json.dumps(body),
            reason_code,
            json.dumps(normalized_references),
            event_hash,
        ),
    ).fetchone()[0]


def append_relation_tx(
    connection,
    contract_id: str,
    organization_id: str,
    relation_type: str,
    source: dict,
    target: dict,
    *,
    actor: Actor,
    reason_code: str | None = None,
) -> str:
    canonical_actor = connection.identity.execute(
        Statement.PROVENANCE_READ_USERS_008,
        (actor.user_id,),
    ).fetchone()
    if canonical_actor != (actor.role.value, actor.organization_id):
        raise ValueError("Relation actor must match canonical identity")
    relation_id = f"relation-{uuid.uuid4().hex}"
    contract = RelationContract.model_validate(
        {
            "id": relation_id,
            "relationType": relation_type,
            "source": source,
            "target": target,
            "actor": {
                "userId": actor.user_id,
                "organizationId": actor.organization_id,
                "role": actor.role.value,
            },
            "reasonCode": reason_code,
        }
    ).model_dump(by_alias=True, mode="json")
    relation_hash = sha256(_canonical(contract).encode()).hexdigest()
    connection.provenance.execute(
        Statement.PROVENANCE_WRITE_PROVENANCE_RELATIONS_009,
        (
            relation_id,
            contract_id,
            organization_id,
            relation_type,
            json.dumps(contract["source"]),
            json.dumps(contract["target"]),
            1,
            actor.user_id,
            actor.role.value,
            actor.organization_id,
            reason_code,
            relation_hash,
        ),
    )
    return relation_id


def append_event(*args, **kwargs) -> int:
    with database() as connection:
        event_id = append_event_tx(connection, *args, **kwargs)
        connection.commit()
    return event_id


def append_lineage(record: LineageInput) -> int:
    with database() as connection:
        lineage_id = append_lineage_tx(connection, record)
        connection.commit()
    return lineage_id


def append_lineage_tx(connection, record: LineageInput) -> int:
    return connection.provenance.execute(Statement.PROVENANCE_WRITE_FIELD_LINEAGE_002,
        (record.contract_id,record.organization_id,record.field_name,json.dumps(record.field_value),
         record.source_artifact_id,record.source_location,record.importer_version,
         record.extractor_provider,record.extractor_model,record.prompt_version,
         record.parser_version,record.mapping_version,record.correction_actor_id,
         record.correction_reason,record.validation_run_id,record.invoice_version_id,
         record.package_artifact_id,record.predecessor_lineage_id),
    ).fetchone()[0]


def audit_query(actor: Actor, contract_id: str, *, submitted: bool) -> dict[str, list[dict]]:
    # `submitted` remains in the additive API for compatibility but is never an
    # authority input. Canonical invoice state controls auditor visibility.
    del submitted
    require_permission(actor, Action.READ, audit_scope(actor, contract_id))
    with database() as connection:
        contract = connection.configuration.execute(Statement.PROVENANCE_READ_CONTRACTS_003, (contract_id,)
        ).fetchone()
        if not contract:
            raise FileNotFoundError(contract_id)
        if actor.role is Role.AUDITOR:
            event_rows = connection.read_models.execute(Statement.PROVENANCE_READ_ARTIFACTS_ARTIFACTS_ARTIFACTS_DOMAIN_EVENTS_004,
                (contract_id,),
            ).fetchall()
            lineage_rows = connection.read_models.execute(Statement.PROVENANCE_READ_ARTIFACTS_FIELD_LINEAGE_INVOICE_VERSIONS_005,
                (contract_id,),
            ).fetchall()
        else:
            event_rows = connection.provenance.execute(Statement.PROVENANCE_READ_DOMAIN_EVENTS_006,
                (contract_id, contract[0], contract[1]),
            ).fetchall()
            lineage_rows = connection.provenance.execute(Statement.PROVENANCE_READ_FIELD_LINEAGE_007, (contract_id,)
            ).fetchall()
        event_rows = connection.provenance.execute(
            Statement.PROVENANCE_READ_DOMAIN_EVENTS_010,
            ([row[0] for row in event_rows],),
        ).fetchall()
        relations = connection.read_models.execute(
            Statement.PROVENANCE_READ_PROVENANCE_RELATIONS_011,
            (contract_id, actor.role is Role.AUDITOR),
        ).fetchall()
        snapshots = connection.read_models.execute(
            Statement.PROVENANCE_READ_INVOICE_SNAPSHOTS_012,
            (contract_id, actor.role is Role.AUDITOR),
        ).fetchall()
    event_keys = ["id","eventKey","eventType","actorId","actorRole","actorOrganizationId","organizationId","contractId","aggregateType","aggregateId","payload","schemaVersion","reasonCode","versionReferences","eventHash","occurredAt"]
    lineage_keys = ["id","fieldName","fieldValue","sourceArtifactId","sourceLocation","importerVersion",
                    "extractorProvider","extractorModel","promptVersion","parserVersion","mappingVersion",
                    "correctionActorId","correctionReason","validationRunId","invoiceVersionId","packageArtifactId",
                    "predecessorLineageId","recordedAt"]
    return {
        "events": [dict(zip(event_keys, row)) for row in event_rows],
        "lineage": [dict(zip(lineage_keys, row)) for row in lineage_rows],
        "relations": [dict(zip(
            ["id","relationType","source","target","actorId","actorRole","actorOrganizationId","reasonCode","relationHash","createdAt"], row
        )) for row in relations],
        "snapshots": [dict(zip(
            ["id","invoiceVersionId","invoiceVersion","materialRevision","stage","payload","snapshotHash","createdBy","actorRole","createdAt"], row
        )) for row in snapshots],
    }
