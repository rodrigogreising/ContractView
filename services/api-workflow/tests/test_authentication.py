from app.authentication import authenticate, identity, resolve_session, revoke_session
from app.authorization import Role
from app.runtime import database


def test_seeded_login_creates_resolvable_opaque_session():
    result = authenticate("ngo.preparer@contractview.demo", "Demo-Prepare-2026!")
    assert result is not None
    token, actor, profile = result
    assert actor.role is Role.NGO_PREPARER
    assert actor.organization_id == "org-ngo"
    assert profile["display_name"] == "Maya Chen"
    assert "ngo.preparer" not in token
    resolved = resolve_session(token)
    assert resolved is not None
    assert resolved[0] == actor
    with database() as connection:
        stored = connection.execute("select token_hash from sessions where user_id = %s order by created_at desc limit 1", (actor.user_id,)).fetchone()[0]
    assert stored != token


def test_identity_preserves_the_public_organization_identifier():
    _, actor, profile = authenticate("ngo.preparer@contractview.demo", "Demo-Prepare-2026!")
    assert identity(actor, profile)["organizationId"] == "org-ngo"


def test_invalid_password_creates_no_session():
    with database() as connection:
        before = connection.execute("select count(*) from sessions").fetchone()[0]
    assert authenticate("ngo.preparer@contractview.demo", "incorrect") is None
    with database() as connection:
        after = connection.execute("select count(*) from sessions").fetchone()[0]
    assert after == before


def test_logout_revokes_server_session_immediately():
    token, _, _ = authenticate("auditor@contractview.demo", "Demo-Audit-2026!")
    assert resolve_session(token) is not None
    revoke_session(token)
    assert resolve_session(token) is None
    with database() as connection:
        event = connection.execute("select event_type from authentication_events order by id desc limit 1").fetchone()[0]
    assert event == "logout"


def test_unknown_or_missing_session_is_rejected():
    assert resolve_session(None) is None
    assert resolve_session("fabricated-browser-storage-value") is None
