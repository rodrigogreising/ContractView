create table artifacts (
    id text primary key,
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    agency_organization_id text not null references organizations(id),
    object_key text not null unique,
    filename text not null,
    media_type text not null,
    byte_size bigint not null check (byte_size >= 0),
    sha256 text not null check (length(sha256) = 64),
    artifact_kind text not null check (artifact_kind in ('original', 'generated')),
    created_by text not null references users(id),
    created_at timestamptz not null default now(),
    submitted boolean not null default false
);

create table artifact_relations (
    predecessor_artifact_id text not null references artifacts(id),
    successor_artifact_id text not null references artifacts(id),
    relation_type text not null check (relation_type in ('replaces', 'regenerates')),
    created_at timestamptz not null default now(),
    primary key(predecessor_artifact_id, successor_artifact_id),
    check(predecessor_artifact_id <> successor_artifact_id)
);

create or replace function reject_artifact_mutation() returns trigger language plpgsql as $$
begin
    raise exception 'artifact records are immutable';
end;
$$;

create trigger artifacts_no_update before update or delete on artifacts
for each row execute function reject_artifact_mutation();

create trigger artifact_relations_no_update before update or delete on artifact_relations
for each row execute function reject_artifact_mutation();
