from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, TypeVar


class Role(StrEnum):
    CONFIGURATION_ADMINISTRATOR = "configuration_administrator"
    NGO_PREPARER = "ngo_preparer"
    NGO_APPROVER = "ngo_approver"
    GOVERNMENT_REVIEWER = "government_reviewer"
    AUDITOR = "auditor"


class ResourceKind(StrEnum):
    CONFIGURATION = "configuration"
    INVOICE = "invoice"
    ARTIFACT = "artifact"
    JOB = "job"
    PACKAGE = "package"
    GOVERNMENT_DECISION = "government_decision"
    AUDIT = "audit"


class Action(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    ACTIVATE = "activate"
    ATTEST = "attest"
    SUBMIT = "submit"
    RETURN = "return"
    APPROVE = "approve"


@dataclass(frozen=True)
class Actor:
    user_id: str
    organization_id: str
    role: Role


@dataclass(frozen=True)
class ResourceScope:
    resource_id: str
    kind: ResourceKind
    owner_organization_id: str
    agency_organization_id: str | None = None
    ngo_organization_id: str | None = None
    submitted: bool = False
    published_to_ngo: bool = False
    contract_id: str | None = None
    canonical: bool = False
    actor_assigned: bool = False


class ForbiddenError(PermissionError):
    pass


def is_allowed(actor: Actor, action: Action, resource: ResourceScope) -> bool:
    # Application code must construct scopes from persisted ownership and
    # assignment data. Caller-authored scope claims always fail closed.
    if not resource.canonical:
        return False

    if actor.role is Role.AUDITOR:
        return (
            resource.actor_assigned
            and resource.submitted
            and action is Action.READ
            and resource.kind in {
                ResourceKind.INVOICE,
                ResourceKind.ARTIFACT,
                ResourceKind.PACKAGE,
                ResourceKind.GOVERNMENT_DECISION,
                ResourceKind.AUDIT,
            }
        )

    if actor.role is Role.CONFIGURATION_ADMINISTRATOR:
        return resource.actor_assigned and resource.kind is ResourceKind.CONFIGURATION and action in {
            Action.READ, Action.CREATE, Action.UPDATE, Action.ACTIVATE
        }

    if actor.role in {Role.NGO_PREPARER, Role.NGO_APPROVER}:
        if resource.ngo_organization_id != actor.organization_id and resource.owner_organization_id != actor.organization_id:
            return False
        if resource.kind is ResourceKind.GOVERNMENT_DECISION:
            return action is Action.READ and resource.published_to_ngo
        if resource.kind is ResourceKind.CONFIGURATION:
            return action is Action.READ and resource.published_to_ngo
        if action is Action.READ:
            return resource.kind in {
                ResourceKind.INVOICE, ResourceKind.ARTIFACT, ResourceKind.JOB,
                ResourceKind.PACKAGE, ResourceKind.AUDIT,
            }
        if actor.role is Role.NGO_PREPARER:
            return action in {Action.CREATE, Action.UPDATE} and resource.kind in {
                ResourceKind.INVOICE, ResourceKind.ARTIFACT, ResourceKind.JOB,
            }
        return action in {Action.ATTEST, Action.SUBMIT} and resource.kind in {
            ResourceKind.INVOICE, ResourceKind.PACKAGE,
        }

    if actor.role is Role.GOVERNMENT_REVIEWER:
        if resource.agency_organization_id != actor.organization_id:
            return False
        if resource.kind is ResourceKind.CONFIGURATION:
            return action is Action.READ and resource.published_to_ngo
        if not resource.submitted:
            return False
        if action is Action.READ:
            return resource.kind in {
                ResourceKind.INVOICE, ResourceKind.ARTIFACT, ResourceKind.PACKAGE,
                ResourceKind.GOVERNMENT_DECISION, ResourceKind.AUDIT,
            }
        return action in {Action.RETURN, Action.APPROVE} and resource.kind in {
            ResourceKind.INVOICE, ResourceKind.PACKAGE, ResourceKind.GOVERNMENT_DECISION,
        }

    return False


def require_permission(actor: Actor, action: Action, resource: ResourceScope) -> None:
    if not is_allowed(actor, action, resource):
        raise ForbiddenError(
            f"{actor.role} cannot {action} {resource.kind}:{resource.resource_id}"
        )


Result = TypeVar("Result")


def execute_authorized(
    actor: Actor,
    action: Action,
    resource: ResourceScope,
    command: Callable[[], Result],
) -> Result:
    """Server command boundary: authorization always precedes mutation."""
    require_permission(actor, action, resource)
    return command()
