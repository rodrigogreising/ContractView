from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .authorization import Actor, Role
from .runtime import database
from .provenance import append_event_tx

SESSION_COOKIE = "contractview_session"
SESSION_TTL = timedelta(hours=8)
_passwords = PasswordHasher()


def _digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def authenticate(email: str, password: str) -> tuple[str, Actor, dict[str, str]] | None:
    with database() as connection:
        row = connection.execute(
            """select u.id, u.organization_id, u.display_name, u.email, u.role,
                      u.password_hash, o.name
               from users u join organizations o on o.id = u.organization_id
               where lower(u.email) = lower(%s) and u.active""",
            (email.strip(),),
        ).fetchone()
        if not row:
            connection.execute("insert into authentication_events(user_id, event_type) values (null, 'login_failed')")
            append_event_tx(connection, "login_failed", "session", "unknown", payload={"email": email.strip().lower()})
            connection.commit()
            return None
        try:
            _passwords.verify(row[5], password)
        except VerifyMismatchError:
            connection.execute("insert into authentication_events(user_id, event_type) values (%s, 'login_failed')", (row[0],))
            append_event_tx(connection, "login_failed", "session", row[0], actor_id=row[0], organization_id=row[1])
            connection.commit()
            return None
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_hex(16)
        expires = datetime.now(timezone.utc) + SESSION_TTL
        connection.execute(
            "insert into sessions(id, token_hash, user_id, expires_at) values (%s, %s, %s, %s)",
            (session_id, _digest(token), row[0], expires),
        )
        connection.execute("insert into authentication_events(user_id, event_type) values (%s, 'login_succeeded')", (row[0],))
        append_event_tx(connection, "login_succeeded", "session", session_id, actor_id=row[0], organization_id=row[1])
        connection.commit()
    actor = Actor(user_id=row[0], organization_id=row[1], role=Role(row[4]))
    return token, actor, {"display_name": row[2], "email": row[3], "organization_name": row[6]}


def resolve_session(token: str | None) -> tuple[Actor, dict[str, str]] | None:
    if not token:
        return None
    with database() as connection:
        row = connection.execute(
            """select u.id, u.organization_id, u.display_name, u.email, u.role, o.name
               from sessions s join users u on u.id = s.user_id
               join organizations o on o.id = u.organization_id
               where s.token_hash = %s and s.revoked_at is null and s.expires_at > now() and u.active""",
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
        row = connection.execute(
            "update sessions set revoked_at = now() where token_hash = %s and revoked_at is null returning user_id",
            (_digest(token),),
        ).fetchone()
        if row:
            connection.execute("insert into authentication_events(user_id, event_type) values (%s, 'logout')", (row[0],))
            user = connection.execute("select organization_id from users where id=%s", (row[0],)).fetchone()
            append_event_tx(connection, "logout", "session", _digest(token)[:16], actor_id=row[0], organization_id=user[0])
        connection.commit()


def identity(actor: Actor, profile: dict[str, str]) -> dict[str, str]:
    return {
        "id": actor.user_id,
        "displayName": profile["display_name"],
        "email": profile["email"],
        "organizationId": actor.organization_id,
        "organizationName": profile["organization_name"],
        "role": actor.role.value,
    }
