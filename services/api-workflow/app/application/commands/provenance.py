from dataclasses import dataclass
import json
from typing import Any

from .access_scope import audit_scope
from ...authorization import Action, Actor, Role, require_permission
from ...shared_contracts import MATERIAL_EVENT_TYPES

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


def append_event_tx(connection, event_type: str, aggregate_type: str, aggregate_id: str, *,
                    actor_id: str | None = None, organization_id: str | None = None,
                    contract_id: str | None = None, payload: dict | None = None) -> int:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unsupported material event: {event_type}")
    return connection.provenance.execute(Statement.PROVENANCE_WRITE_DOMAIN_EVENTS_001,
        (event_type, actor_id, organization_id, contract_id, aggregate_type, aggregate_id, json.dumps(payload or {})),
    ).fetchone()[0]


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
    event_keys = ["id","eventType","actorId","organizationId","aggregateType","aggregateId","payload","occurredAt"]
    lineage_keys = ["id","fieldName","fieldValue","sourceArtifactId","sourceLocation","importerVersion",
                    "extractorProvider","extractorModel","promptVersion","parserVersion","mappingVersion",
                    "correctionActorId","correctionReason","validationRunId","invoiceVersionId","packageArtifactId",
                    "predecessorLineageId","recordedAt"]
    return {
        "events": [dict(zip(event_keys, row)) for row in event_rows],
        "lineage": [dict(zip(lineage_keys, row)) for row in lineage_rows],
    }
