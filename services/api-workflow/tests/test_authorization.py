import pytest

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

def resource(kind=ResourceKind.INVOICE, *, owner=NGO, submitted=False, published=False):
    return ResourceScope("resource-1", kind, owner, AGENCY, owner, submitted, published)

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
    other_agency = ResourceScope("invoice-2", ResourceKind.INVOICE, NGO, "other-agency", NGO, True)
    assert not is_allowed(REVIEWER, Action.READ, other_agency)

def test_government_decision_is_hidden_from_ngo_until_published() -> None:
    private = resource(ResourceKind.GOVERNMENT_DECISION, submitted=True)
    published = resource(ResourceKind.GOVERNMENT_DECISION, submitted=True, published=True)
    assert is_allowed(REVIEWER, Action.READ, private)
    assert not is_allowed(PREPARER, Action.READ, private)
    assert is_allowed(PREPARER, Action.READ, published)

def test_configuration_is_administered_only_by_configuration_role() -> None:
    configuration = resource(ResourceKind.CONFIGURATION, owner="org-operations")
    assert is_allowed(ADMIN, Action.ACTIVATE, configuration)
    assert not is_allowed(PREPARER, Action.UPDATE, configuration)
    assert not is_allowed(REVIEWER, Action.ACTIVATE, configuration)

def test_auditor_is_global_read_only_for_synthetic_poc() -> None:
    assert is_allowed(AUDITOR, Action.READ, resource(ResourceKind.AUDIT))
    assert is_allowed(AUDITOR, Action.READ, resource(ResourceKind.PACKAGE, submitted=True))
    assert not is_allowed(AUDITOR, Action.UPDATE, resource())
    assert not is_allowed(AUDITOR, Action.APPROVE, resource(submitted=True))

@pytest.mark.parametrize("kind", list(ResourceKind))
def test_indirect_reference_denial_never_invokes_mutation(kind: ResourceKind) -> None:
    mutations: list[str] = []
    cross_org = ResourceScope("guessed-id", kind, OTHER_NGO, AGENCY, OTHER_NGO, True)
    with pytest.raises(ForbiddenError):
        execute_authorized(PREPARER, Action.UPDATE, cross_org, lambda: mutations.append("changed"))
    assert mutations == []

def test_role_authority_is_separated() -> None:
    submitted = resource(ResourceKind.PACKAGE, submitted=True)
    assert not is_allowed(PREPARER, Action.SUBMIT, submitted)
    assert is_allowed(APPROVER, Action.SUBMIT, submitted)
    assert not is_allowed(APPROVER, Action.APPROVE, submitted)
    assert is_allowed(REVIEWER, Action.APPROVE, submitted)
