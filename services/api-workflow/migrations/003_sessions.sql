create table sessions (
    id text primary key,
    token_hash text not null unique,
    user_id text not null references users(id),
    created_at timestamptz not null default now(),
    expires_at timestamptz not null,
    revoked_at timestamptz
);

create index sessions_active_token_idx on sessions(token_hash) where revoked_at is null;

create table authentication_events (
    id bigserial primary key,
    user_id text references users(id),
    event_type text not null check (event_type in ('login_succeeded', 'login_failed', 'logout')),
    occurred_at timestamptz not null default now()
);
