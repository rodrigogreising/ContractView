from app.authentication import authenticate, identity, resolve_session, revoke_session
from app.authorization import Role
from app.runtime import database
from app.access_scope import contract_contexts
from app.authorization import Actor


def test_seeded_login_creates_resolvable_opaque_session():
    result = authenticate("ngo.preparer@example.test", "Demo-Prepare-2026!")
    assert result is not None
    token, actor, profile = result
    assert actor.role is Role.NGO_PREPARER
    assert actor.organization_id == "org-ngo"
    assert profile["display_name"] == "Synthetic NGO Preparer"
    assert "ngo.preparer" not in token
    resolved = resolve_session(token)
    assert resolved is not None
    assert resolved[0] == actor
    with database() as connection:
        stored = connection.execute("select token_hash from sessions where user_id = %s order by created_at desc limit 1", (actor.user_id,)).fetchone()[0]
    assert stored != token


def test_identity_preserves_the_public_organization_identifier():
    _, actor, profile = authenticate("ngo.preparer@example.test", "Demo-Prepare-2026!")
    assert identity(actor, profile)["organizationId"] == "org-ngo"


def test_invalid_password_creates_no_session():
    with database() as connection:
        before = connection.execute("select count(*) from sessions").fetchone()[0]
    assert authenticate("ngo.preparer@example.test", "incorrect") is None
    with database() as connection:
        after = connection.execute("select count(*) from sessions").fetchone()[0]
    assert after == before


def test_logout_revokes_server_session_immediately():
    token, _, _ = authenticate("auditor@example.test", "Demo-Audit-2026!")
    assert resolve_session(token) is not None
    revoke_session(token)
    assert resolve_session(token) is None
    with database() as connection:
        event = connection.execute("select event_type from authentication_events order by id desc limit 1").fetchone()[0]
    assert event == "logout"


def test_unknown_or_missing_session_is_rejected():
    assert resolve_session(None) is None
    assert resolve_session("fabricated-browser-storage-value") is None


def test_contract_context_is_derived_from_canonical_session_scope():
    cases = [
        ("configuration.admin@example.test", "Demo-Config-2026!"),
        ("ngo.preparer@example.test", "Demo-Prepare-2026!"),
        ("ngo.approver@example.test", "Demo-Approve-2026!"),
        ("government.reviewer@example.test", "Demo-Review-2026!"),
        ("auditor@example.test", "Demo-Audit-2026!"),
    ]
    for email, password in cases:
        _, actor, _ = authenticate(email, password)
        contexts = contract_contexts(actor)
        by_id = {context["contractId"]: context for context in contexts}
        assert by_id["contract-synthetic-agency-ngo-2026"] == {
            "contractId": "contract-synthetic-agency-ngo-2026",
            "contractName": "Synthetic Community Services Contract 2026",
            "agencyOrganizationId": "org-government",
            "agencyOrganizationName": "Synthetic Public Agency",
            "ngoOrganizationId": "org-ngo",
            "ngoOrganizationName": "Synthetic Community Nonprofit",
        }
        if actor.role in {Role.NGO_PREPARER, Role.NGO_APPROVER}:
            assert all(item["ngoOrganizationId"] == actor.organization_id for item in contexts)
        if actor.role is Role.GOVERNMENT_REVIEWER:
            assert all(item["agencyOrganizationId"] == actor.organization_id for item in contexts)
    assert contract_contexts(
        Actor("outside-reviewer", "org-other", Role.GOVERNMENT_REVIEWER)
    ) == []
