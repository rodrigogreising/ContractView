from dataclasses import asdict, dataclass
import json
from typing import Any

from .access_scope import audit_scope
from .authorization import Action, Actor, Role, require_permission
from .runtime import database

EVENT_TYPES = {
    "login_succeeded", "login_failed", "logout", "config_activated", "artifact_uploaded",
    "extraction_drafted", "extraction_failed", "field_corrected", "field_reviewed", "validation_completed",
    "attested", "package_generated", "submitted", "returned", "revision_created",
    "resubmitted", "approved",
    "invoice_line_corrected", "finding_resolved",
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
    with database() as connection:
        lineage_id = append_lineage_tx(connection, record)
        connection.commit()
    return lineage_id


def append_lineage_tx(connection, record: LineageInput) -> int:
    values = asdict(record)
    values["field_value"] = json.dumps(record.field_value)
    columns = list(values)
    return connection.execute(
        f"insert into field_lineage ({','.join(columns)}) values ({','.join(['%s'] * len(columns))}) returning id",
        tuple(values[column] for column in columns),
    ).fetchone()[0]


def audit_query(actor: Actor, contract_id: str, *, submitted: bool) -> dict[str, list[dict]]:
    # `submitted` remains in the additive API for compatibility but is never an
    # authority input. Canonical invoice state controls auditor visibility.
    del submitted
    require_permission(actor, Action.READ, audit_scope(actor, contract_id))
    with database() as connection:
        contract = connection.execute(
            "select ngo_organization_id, agency_organization_id from contracts where id=%s", (contract_id,)
        ).fetchone()
        if not contract:
            raise FileNotFoundError(contract_id)
        if actor.role is Role.AUDITOR:
            event_rows = connection.execute(
                """select e.id,e.event_type,e.actor_id,e.organization_id,e.aggregate_type,
                          e.aggregate_id,e.payload,e.occurred_at
                   from domain_events e
                   where e.contract_id=%s and (
                     (e.aggregate_type='artifact' and exists(
                       select 1 from artifacts a where a.id=e.aggregate_id and a.submitted=true))
                     or (e.aggregate_type='configuration_version' and exists(
                       select 1 from invoice_versions i
                       where i.configuration_version_id=e.aggregate_id and i.state<>'draft'))
                     or (e.aggregate_type='extraction_run' and exists(
                       select 1 from extraction_runs x join artifacts a on a.id=x.source_artifact_id
                       where x.id=e.aggregate_id and a.submitted=true))
                     or (e.aggregate_type='extraction_field' and exists(
                       select 1 from extraction_fields f join extraction_runs x on x.id=f.extraction_run_id
                       join artifacts a on a.id=x.source_artifact_id
                       where f.id=e.aggregate_id and a.submitted=true))
                     or (e.aggregate_type='validation_run' and exists(
                       select 1 from validation_runs v join invoice_versions i on i.id=v.invoice_version_id
                       where v.id=e.aggregate_id and i.state<>'draft'))
                     or (e.aggregate_type='invoice_line' and exists(
                       select 1 from invoice_lines l join invoice_versions i on i.id=l.invoice_version_id
                       where l.id=e.aggregate_id and i.state<>'draft'))
                     or (e.aggregate_type='validation_finding' and exists(
                       select 1 from validation_findings f join invoice_versions i on i.id=f.invoice_version_id
                       where f.id=e.aggregate_id and i.state<>'draft'))
                     or (e.aggregate_type='invoice_version' and exists(
                       select 1 from invoice_versions i where i.id=e.aggregate_id and i.state<>'draft'))
                     or (e.aggregate_type='package' and exists(
                       select 1 from packages p join invoice_versions i on i.id=p.invoice_version_id
                       where p.id=e.aggregate_id and i.state<>'draft'))
                   ) order by e.id""",
                (contract_id,),
            ).fetchall()
            lineage_rows = connection.execute(
                """select l.id,l.field_name,l.field_value,l.source_artifact_id,l.source_location,
                          l.importer_version,l.extractor_provider,l.extractor_model,l.prompt_version,
                          l.parser_version,l.mapping_version,l.correction_actor_id,l.correction_reason,
                          l.validation_run_id,l.invoice_version_id,l.package_artifact_id,
                          l.predecessor_lineage_id,l.recorded_at
                   from field_lineage l where l.contract_id=%s and (
                     (l.invoice_version_id is not null and exists(
                       select 1 from invoice_versions i
                       where i.id=l.invoice_version_id and i.state<>'draft'))
                     or (l.invoice_version_id is null and l.source_artifact_id is not null and exists(
                       select 1 from artifacts a where a.id=l.source_artifact_id and a.submitted=true))
                   ) order by l.id""",
                (contract_id,),
            ).fetchall()
        else:
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
