from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets

from ...authorization import Actor, Role
from .provenance import append_event_tx
from ...shared_contracts import IdentityDto

from ..passwords import password_matches
from ..ports.statements import Statement
from ..transaction import transaction as database
SESSION_COOKIE = "contractview_session"
SESSION_TTL = timedelta(hours=8)


def _digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def authenticate(email: str, password: str) -> tuple[str, Actor, dict[str, str]] | None:
    with database() as connection:
        row = connection.identity.execute(Statement.AUTHENTICATION_READ_ORGANIZATIONS_USERS_001,
            (email.strip(),),
        ).fetchone()
        if not row:
            connection.identity.execute(Statement.AUTHENTICATION_WRITE_AUTHENTICATION_EVENTS_002)
            append_event_tx(connection, "login_failed", "session", "unknown", payload={"email": email.strip().lower()})
            connection.commit()
            return None
        if not password_matches(row[5], password):
            connection.identity.execute(Statement.AUTHENTICATION_WRITE_AUTHENTICATION_EVENTS_003, (row[0],))
            append_event_tx(connection, "login_failed", "session", row[0], actor_id=row[0], organization_id=row[1])
            connection.commit()
            return None
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_hex(16)
        expires = datetime.now(timezone.utc) + SESSION_TTL
        connection.identity.execute(Statement.AUTHENTICATION_WRITE_SESSIONS_004,
            (session_id, _digest(token), row[0], expires),
        )
        connection.identity.execute(Statement.AUTHENTICATION_WRITE_AUTHENTICATION_EVENTS_005, (row[0],))
        append_event_tx(connection, "login_succeeded", "session", session_id, actor_id=row[0], organization_id=row[1])
        connection.commit()
    actor = Actor(user_id=row[0], organization_id=row[1], role=Role(row[4]))
    return token, actor, {"display_name": row[2], "email": row[3], "organization_name": row[6]}


def resolve_session(token: str | None) -> tuple[Actor, dict[str, str]] | None:
    if not token:
        return None
    with database() as connection:
        row = connection.identity.execute(Statement.AUTHENTICATION_READ_ORGANIZATIONS_SESSIONS_USERS_006,
            (_digest(token),),
        ).fetchone()
    if not row:
        return None
    return Actor(user_id=row[0], organization_id=row[1], role=Role(row[4])), {
        "display_name": row[2], "email": row[3], "organization_name": row[5]
    }


def revoke_session(token: str | None) -> None:
    if not token:
        return
    with database() as connection:
        row = connection.identity.execute(Statement.AUTHENTICATION_WRITE_SESSIONS_007,
            (_digest(token),),
        ).fetchone()
        if row:
            connection.identity.execute(Statement.AUTHENTICATION_WRITE_AUTHENTICATION_EVENTS_008, (row[0],))
            user = connection.identity.execute(Statement.AUTHENTICATION_READ_USERS_009, (row[0],)).fetchone()
            if not user:raise RuntimeError("Session user is missing")
            append_event_tx(connection, "logout", "session", _digest(token)[:16], actor_id=row[0], organization_id=user[0])
        connection.commit()


def identity(actor: Actor, profile: dict[str, str]) -> dict[str, str]:
    return IdentityDto(
        id=actor.user_id,
        display_name=profile["display_name"],
        email=profile["email"],
        organization_id=actor.organization_id,
        organization_name=profile["organization_name"],
        role=actor.role,
    ).model_dump(by_alias=True)
