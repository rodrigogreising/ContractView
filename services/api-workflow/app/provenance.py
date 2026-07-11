from dataclasses import asdict, dataclass
import json
from typing import Any

from .authorization import Action, Actor, ResourceKind, ResourceScope, require_permission
from .runtime import database

EVENT_TYPES = {
    "login_succeeded", "login_failed", "logout", "config_activated", "artifact_uploaded",
    "extraction_drafted", "extraction_failed", "field_corrected", "validation_completed",
    "attested", "package_generated", "submitted", "returned", "revision_created",
    "resubmitted", "approved",
}


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
    return connection.execute(
        """insert into domain_events
           (event_type, actor_id, organization_id, contract_id, aggregate_type, aggregate_id, payload)
           values (%s,%s,%s,%s,%s,%s,%s) returning id""",
        (event_type, actor_id, organization_id, contract_id, aggregate_type, aggregate_id, json.dumps(payload or {})),
    ).fetchone()[0]


def append_event(*args, **kwargs) -> int:
    with database() as connection:
        event_id = append_event_tx(connection, *args, **kwargs)
        connection.commit()
    return event_id


def append_lineage(record: LineageInput) -> int:
    values = asdict(record)
    values["field_value"] = json.dumps(record.field_value)
    columns = list(values)
    with database() as connection:
        lineage_id = connection.execute(
            f"insert into field_lineage ({','.join(columns)}) values ({','.join(['%s'] * len(columns))}) returning id",
            tuple(values[column] for column in columns),
        ).fetchone()[0]
        connection.commit()
    return lineage_id


def audit_query(actor: Actor, contract_id: str, *, submitted: bool) -> dict[str, list[dict]]:
    with database() as connection:
        contract = connection.execute(
            "select ngo_organization_id, agency_organization_id from contracts where id=%s", (contract_id,)
        ).fetchone()
        if not contract:
            raise FileNotFoundError(contract_id)
        scope = ResourceScope(
            f"audit:{contract_id}", ResourceKind.AUDIT, contract[0],
            agency_organization_id=contract[1], ngo_organization_id=contract[0], submitted=submitted,
        )
        require_permission(actor, Action.READ, scope)
        event_rows = connection.execute(
            """select id, event_type, actor_id, organization_id, aggregate_type, aggregate_id, payload, occurred_at
               from domain_events
               where contract_id=%s or (contract_id is null and organization_id in (%s,%s)) order by id""",
            (contract_id, contract[0], contract[1]),
        ).fetchall()
        lineage_rows = connection.execute(
            """select id, field_name, field_value, source_artifact_id, source_location,
                      importer_version, extractor_provider, extractor_model, prompt_version,
                      parser_version, mapping_version, correction_actor_id, correction_reason,
                      validation_run_id, invoice_version_id, package_artifact_id,
                      predecessor_lineage_id, recorded_at
               from field_lineage where contract_id=%s order by id""", (contract_id,)
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
