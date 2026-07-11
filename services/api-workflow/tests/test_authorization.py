import pytest
from itertools import product

from app.authorization import (
    Action, Actor, ForbiddenError, ResourceKind, ResourceScope, Role,
    execute_authorized, is_allowed,
)

AGENCY = "org-government"
NGO = "org-ngo"
OTHER_NGO = "org-other-ngo"

PREPARER = Actor("user-ngo-preparer", NGO, Role.NGO_PREPARER)
APPROVER = Actor("user-ngo-approver", NGO, Role.NGO_APPROVER)
REVIEWER = Actor("user-government-reviewer", AGENCY, Role.GOVERNMENT_REVIEWER)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)

def resource(kind=ResourceKind.INVOICE, *, owner=NGO, submitted=False, published=False, assigned=True):
    return ResourceScope(
        "resource-1", kind, owner, AGENCY, owner, submitted, published,
        contract_id="contract-1", canonical=True, actor_assigned=assigned,
    )

def test_ngo_roles_are_scoped_to_their_organization() -> None:
    assert is_allowed(PREPARER, Action.UPDATE, resource())
    assert is_allowed(APPROVER, Action.SUBMIT, resource())
    other = resource(owner=OTHER_NGO)
    assert not is_allowed(PREPARER, Action.READ, other)
    assert not is_allowed(APPROVER, Action.SUBMIT, other)

def test_government_can_read_and_decide_only_submitted_agency_resources() -> None:
    assert not is_allowed(REVIEWER, Action.READ, resource(submitted=False))
    submitted = resource(submitted=True)
    assert is_allowed(REVIEWER, Action.READ, submitted)
    assert is_allowed(REVIEWER, Action.RETURN, submitted)
    assert is_allowed(REVIEWER, Action.APPROVE, submitted)
    other_agency = ResourceScope(
        "invoice-2", ResourceKind.INVOICE, NGO, "other-agency", NGO, True,
        contract_id="contract-2", canonical=True, actor_assigned=True,
    )
    assert not is_allowed(REVIEWER, Action.READ, other_agency)

def test_government_decision_is_hidden_from_ngo_until_published() -> None:
    private = resource(ResourceKind.GOVERNMENT_DECISION, submitted=True)
    published = resource(ResourceKind.GOVERNMENT_DECISION, submitted=True, published=True)
    assert is_allowed(REVIEWER, Action.READ, private)
    assert not is_allowed(PREPARER, Action.READ, private)
    assert is_allowed(PREPARER, Action.READ, published)

def test_configuration_is_administered_only_by_configuration_role() -> None:
    configuration = resource(ResourceKind.CONFIGURATION, owner=AGENCY)
    assert is_allowed(ADMIN, Action.ACTIVATE, configuration)
    assert not is_allowed(ADMIN, Action.ACTIVATE, resource(ResourceKind.CONFIGURATION, assigned=False))
    assert not is_allowed(PREPARER, Action.UPDATE, configuration)
    assert not is_allowed(REVIEWER, Action.ACTIVATE, configuration)

def test_auditor_requires_assignment_and_submitted_visibility() -> None:
    assert not is_allowed(AUDITOR, Action.READ, resource(ResourceKind.AUDIT))
    assert not is_allowed(AUDITOR, Action.READ, resource(ResourceKind.AUDIT, submitted=True, assigned=False))
    assert is_allowed(AUDITOR, Action.READ, resource(ResourceKind.AUDIT, submitted=True))
    assert is_allowed(AUDITOR, Action.READ, resource(ResourceKind.PACKAGE, submitted=True))
    assert not is_allowed(AUDITOR, Action.READ, resource(ResourceKind.JOB, submitted=True))
    assert not is_allowed(AUDITOR, Action.READ, resource(ResourceKind.CONFIGURATION, submitted=True))
    assert not is_allowed(AUDITOR, Action.UPDATE, resource())
    assert not is_allowed(AUDITOR, Action.APPROVE, resource(submitted=True))

@pytest.mark.parametrize("kind", list(ResourceKind))
def test_indirect_reference_denial_never_invokes_mutation(kind: ResourceKind) -> None:
    mutations: list[str] = []
    cross_org = ResourceScope(
        "guessed-id", kind, OTHER_NGO, AGENCY, OTHER_NGO, True,
        contract_id="contract-other", canonical=True, actor_assigned=True,
    )
    with pytest.raises(ForbiddenError):
        execute_authorized(PREPARER, Action.UPDATE, cross_org, lambda: mutations.append("changed"))
    assert mutations == []

def test_role_authority_is_separated() -> None:
    submitted = resource(ResourceKind.PACKAGE, submitted=True)
    assert not is_allowed(PREPARER, Action.SUBMIT, submitted)
    assert is_allowed(APPROVER, Action.SUBMIT, submitted)
    assert not is_allowed(APPROVER, Action.APPROVE, submitted)
    assert is_allowed(REVIEWER, Action.APPROVE, submitted)


def test_caller_authored_scope_claims_fail_closed() -> None:
    claimed = ResourceScope(
        "caller-value", ResourceKind.INVOICE, NGO,
        agency_organization_id=AGENCY, ngo_organization_id=NGO, submitted=True,
    )
    for actor in (PREPARER, APPROVER, REVIEWER, AUDITOR, ADMIN):
        for action in Action:
            assert not is_allowed(actor, action, claimed)


@pytest.mark.parametrize("role", list(Role))
@pytest.mark.parametrize("kind", list(ResourceKind))
@pytest.mark.parametrize("submitted", [False, True])
def test_role_resource_matrix_never_grants_unassigned_privileged_access(
    role: Role, kind: ResourceKind, submitted: bool
) -> None:
    actor = Actor(f"matrix-{role}", NGO if role in {Role.NGO_PREPARER, Role.NGO_APPROVER} else AGENCY, role)
    scope = resource(kind, submitted=submitted, assigned=False)
    if role in {Role.CONFIGURATION_ADMINISTRATOR, Role.AUDITOR}:
        assert not is_allowed(actor, Action.READ, scope)


def test_exhaustive_role_tenant_resource_action_matrix() -> None:
    actors = (PREPARER, APPROVER, REVIEWER, AUDITOR, ADMIN)
    evaluated = 0
    for actor, kind, action, tenant_match, submitted, published, assigned in product(
        actors, ResourceKind, Action, (False, True), (False, True), (False, True), (False, True)
    ):
        ngo_id = actor.organization_id if tenant_match and actor.role in {Role.NGO_PREPARER, Role.NGO_APPROVER} else NGO
        if actor.role in {Role.NGO_PREPARER, Role.NGO_APPROVER} and not tenant_match:
            ngo_id = OTHER_NGO
        agency_id = actor.organization_id if tenant_match and actor.role is Role.GOVERNMENT_REVIEWER else AGENCY
        if actor.role is Role.GOVERNMENT_REVIEWER and not tenant_match:
            agency_id = "other-agency"
        scope = ResourceScope(
            "matrix-resource", kind, ngo_id,
            agency_organization_id=agency_id,
            ngo_organization_id=ngo_id,
            submitted=submitted,
            published_to_ngo=published,
            contract_id="matrix-contract",
            canonical=True,
            actor_assigned=assigned,
        )

        if actor.role is Role.AUDITOR:
            expected = assigned and submitted and action is Action.READ and kind in {
                ResourceKind.INVOICE, ResourceKind.ARTIFACT, ResourceKind.PACKAGE,
                ResourceKind.GOVERNMENT_DECISION, ResourceKind.AUDIT,
            }
        elif actor.role is Role.CONFIGURATION_ADMINISTRATOR:
            expected = assigned and kind is ResourceKind.CONFIGURATION and action in {
                Action.READ, Action.CREATE, Action.UPDATE, Action.ACTIVATE,
            }
        elif actor.role in {Role.NGO_PREPARER, Role.NGO_APPROVER}:
            expected = False
            if tenant_match:
                if kind is ResourceKind.GOVERNMENT_DECISION:
                    expected = action is Action.READ and published
                elif kind is ResourceKind.CONFIGURATION:
                    expected = action is Action.READ and published
                elif action is Action.READ:
                    expected = kind in {
                        ResourceKind.INVOICE, ResourceKind.ARTIFACT, ResourceKind.JOB,
                        ResourceKind.PACKAGE, ResourceKind.AUDIT,
                    }
                elif actor.role is Role.NGO_PREPARER:
                    expected = action in {Action.CREATE, Action.UPDATE} and kind in {
                        ResourceKind.INVOICE, ResourceKind.ARTIFACT, ResourceKind.JOB,
                    }
                else:
                    expected = action in {Action.ATTEST, Action.SUBMIT} and kind in {
                        ResourceKind.INVOICE, ResourceKind.PACKAGE,
                    }
        else:
            expected = False
            if tenant_match and kind is ResourceKind.CONFIGURATION:
                expected = action is Action.READ and published
            elif tenant_match and submitted:
                if action is Action.READ:
                    expected = kind in {
                        ResourceKind.INVOICE, ResourceKind.ARTIFACT, ResourceKind.PACKAGE,
                        ResourceKind.GOVERNMENT_DECISION, ResourceKind.AUDIT,
                    }
                else:
                    expected = action in {Action.RETURN, Action.APPROVE} and kind in {
                        ResourceKind.INVOICE, ResourceKind.PACKAGE, ResourceKind.GOVERNMENT_DECISION,
                    }

        assert is_allowed(actor, action, scope) is expected, (
            actor.role, kind, action, tenant_match, submitted, published, assigned
        )
        evaluated += 1
    assert evaluated == 4480
