"""Canonical authorization-scope resolution.

Every public resolver derives ownership, lifecycle visibility, and explicit
assignments from persisted records. HTTP parameters and actor organization
claims never become resource ownership facts.
"""

from typing import Any

from .authorization import Actor, ResourceKind, ResourceScope
from .runtime import database


def _contract(connection: Any, contract_id: str) -> tuple[str, str]:
    row = connection.execute(
        "select agency_organization_id, ngo_organization_id from contracts where id=%s",
        (contract_id,),
    ).fetchone()
    if not row:
        raise FileNotFoundError(contract_id)
    return row[0], row[1]


def _is_assigned(connection: Any, actor: Actor, contract_id: str, agency_id: str) -> bool:
    return bool(
        connection.execute(
            """select 1
               from contract_role_assignments a
               join users u on u.id=a.user_id
               where a.contract_id=%s and a.user_id=%s and a.role=%s
                 and a.agency_organization_id=%s
                 and u.organization_id=%s and u.role=%s and u.active=true""",
            (
                contract_id,
                actor.user_id,
                actor.role.value,
                agency_id,
                actor.organization_id,
                actor.role.value,
            ),
        ).fetchone()
    )


def _build(
    connection: Any,
    actor: Actor,
    contract_id: str,
    resource_id: str,
    kind: ResourceKind,
    *,
    submitted: bool = False,
    published_to_ngo: bool = False,
) -> ResourceScope:
    agency_id, ngo_id = _contract(connection, contract_id)
    owner_id = agency_id if kind is ResourceKind.CONFIGURATION else ngo_id
    return ResourceScope(
        resource_id=resource_id,
        kind=kind,
        owner_organization_id=owner_id,
        agency_organization_id=agency_id,
        ngo_organization_id=ngo_id,
        submitted=submitted,
        published_to_ngo=published_to_ngo,
        contract_id=contract_id,
        canonical=True,
        actor_assigned=_is_assigned(connection, actor, contract_id, agency_id),
    )


def contract_scope(actor: Actor, contract_id: str, resource_id: str, kind: ResourceKind) -> ResourceScope:
    """Resolve a not-yet-created contract resource from the canonical contract."""
    with database() as connection:
        return _build(connection, actor, contract_id, resource_id, kind)


def configuration_scope(actor: Actor, contract_id: str, *, active_only: bool = False) -> ResourceScope:
    with database() as connection:
        active = False
        if active_only:
            active = bool(
                connection.execute(
                    "select 1 from configuration_versions where contract_id=%s and status='active' limit 1",
                    (contract_id,),
                ).fetchone()
            )
        return _build(
            connection,
            actor,
            contract_id,
            f"configuration:{contract_id}",
            ResourceKind.CONFIGURATION,
            published_to_ngo=active,
        )


def invoice_scope(actor: Actor, invoice_id: str, *, kind: ResourceKind = ResourceKind.INVOICE) -> ResourceScope:
    with database() as connection:
        row = connection.execute(
            "select contract_id, state from invoice_versions where id=%s", (invoice_id,)
        ).fetchone()
        if not row:
            raise FileNotFoundError(invoice_id)
        return _build(connection, actor, row[0], invoice_id, kind, submitted=row[1] != "draft")


def artifact_scope(actor: Actor, artifact_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.execute(
            "select contract_id, submitted from artifacts where id=%s", (artifact_id,)
        ).fetchone()
        if not row:
            raise FileNotFoundError(artifact_id)
        return _build(connection, actor, row[0], artifact_id, ResourceKind.ARTIFACT, submitted=row[1])


def job_scope(actor: Actor, job_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.execute("select contract_id from ingestion_jobs where id=%s", (job_id,)).fetchone()
        if not row:
            raise FileNotFoundError(job_id)
        return _build(connection, actor, row[0], job_id, ResourceKind.JOB)


def extraction_scope(actor: Actor, extraction_run_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.execute(
            "select contract_id from extraction_runs where id=%s", (extraction_run_id,)
        ).fetchone()
        if not row:
            raise FileNotFoundError(extraction_run_id)
        return _build(connection, actor, row[0], extraction_run_id, ResourceKind.JOB)


def government_decision_scope(actor: Actor, queue_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.execute(
            """select iv.contract_id, q.status
               from government_queue_items q
               join submissions s on s.id=q.submission_id
               join invoice_versions iv on iv.id=s.invoice_version_id
               where q.id=%s""",
            (queue_id,),
        ).fetchone()
        if not row:
            raise FileNotFoundError(queue_id)
        return _build(
            connection,
            actor,
            row[0],
            queue_id,
            ResourceKind.GOVERNMENT_DECISION,
            submitted=True,
            published_to_ngo=row[1] in {"returned", "approved"},
        )


def audit_scope(actor: Actor, contract_id: str) -> ResourceScope:
    with database() as connection:
        submitted = bool(
            connection.execute(
                "select 1 from invoice_versions where contract_id=%s and state <> 'draft' limit 1",
                (contract_id,),
            ).fetchone()
        )
        return _build(
            connection,
            actor,
            contract_id,
            f"audit:{contract_id}",
            ResourceKind.AUDIT,
            submitted=submitted,
        )
