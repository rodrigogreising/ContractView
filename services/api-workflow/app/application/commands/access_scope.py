from ..ports.statements import Statement
from ..transaction import transaction as database
"""Canonical authorization-scope resolution.

Every public resolver derives ownership, lifecycle visibility, and explicit
assignments from persisted records. HTTP parameters and actor organization
claims never become resource ownership facts.
"""

from typing import Any

from ...authorization import Actor, ResourceKind, ResourceScope
from ...shared_contracts import ContractContextDto


def _contract(connection: Any, contract_id: str) -> tuple[str, str]:
    row = connection.configuration.execute(Statement.ACCESS_SCOPE_READ_CONTRACTS_001,
        (contract_id,),
    ).fetchone()
    if not row:
        raise FileNotFoundError(contract_id)
    return row[0], row[1]


def _is_assigned(connection: Any, actor: Actor, contract_id: str, agency_id: str) -> bool:
    return bool(
        connection.identity.execute(Statement.ACCESS_SCOPE_READ_CONTRACT_ROLE_ASSIGNMENTS_USERS_002,
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


def contract_contexts(actor: Actor) -> list[dict[str, str]]:
    """Return only contract contexts authorized by canonical session scope."""
    role = actor.role.value
    with database() as connection:
        rows = connection.read_models.execute(
            Statement.ACCESS_SCOPE_READ_CONTRACTS_CONTRACT_ROLE_ASSIGNMENTS_ORGANIZATIONS_USERS_010,
            (
                role,
                actor.user_id,
                role,
                role,
                actor.organization_id,
                role,
                actor.organization_id,
            ),
        ).fetchall()
    return [
        ContractContextDto(
            contract_id=row[0],
            contract_name=row[1],
            agency_organization_id=row[2],
            agency_organization_name=row[3],
            ngo_organization_id=row[4],
            ngo_organization_name=row[5],
        ).model_dump(by_alias=True)
        for row in rows
    ]


def contract_scope(actor: Actor, contract_id: str, resource_id: str, kind: ResourceKind) -> ResourceScope:
    """Resolve a not-yet-created contract resource from the canonical contract."""
    with database() as connection:
        return _build(connection, actor, contract_id, resource_id, kind)


def configuration_scope(actor: Actor, contract_id: str, *, active_only: bool = False) -> ResourceScope:
    with database() as connection:
        active = False
        if active_only:
            active = bool(
                connection.configuration.execute(Statement.ACCESS_SCOPE_READ_CONFIGURATION_VERSIONS_003,
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
        row = connection.invoices.execute(Statement.ACCESS_SCOPE_READ_INVOICE_VERSIONS_004, (invoice_id,)
        ).fetchone()
        if not row:
            raise FileNotFoundError(invoice_id)
        return _build(connection, actor, row[0], invoice_id, kind, submitted=row[1] != "draft")


def artifact_scope(actor: Actor, artifact_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.artifacts.execute(Statement.ACCESS_SCOPE_READ_ARTIFACTS_005, (artifact_id,)
        ).fetchone()
        if not row:
            raise FileNotFoundError(artifact_id)
        return _build(connection, actor, row[0], artifact_id, ResourceKind.ARTIFACT, submitted=row[1])


def job_scope(actor: Actor, job_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.extraction.execute(Statement.ACCESS_SCOPE_READ_INGESTION_JOBS_006, (job_id,)).fetchone()
        if not row:
            raise FileNotFoundError(job_id)
        return _build(connection, actor, row[0], job_id, ResourceKind.JOB)


def extraction_scope(actor: Actor, extraction_run_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.extraction.execute(Statement.ACCESS_SCOPE_READ_EXTRACTION_RUNS_007, (extraction_run_id,)
        ).fetchone()
        if not row:
            raise FileNotFoundError(extraction_run_id)
        return _build(connection, actor, row[0], extraction_run_id, ResourceKind.JOB)


def government_decision_scope(actor: Actor, queue_id: str) -> ResourceScope:
    with database() as connection:
        row = connection.read_models.execute(Statement.ACCESS_SCOPE_READ_GOVERNMENT_QUEUE_ITEMS_INVOICE_VERSIONS_SUBMISSIONS_008,
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
            connection.invoices.execute(Statement.ACCESS_SCOPE_READ_INVOICE_VERSIONS_009,
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
