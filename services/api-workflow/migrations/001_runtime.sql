create table poc_metadata (key text primary key, value text not null);
create table worker_heartbeat (worker_name text primary key, last_seen_at timestamptz not null);
