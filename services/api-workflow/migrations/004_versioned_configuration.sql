create table configuration_drafts (
    contract_id text primary key references contracts(id),
    payload jsonb not null,
    updated_by text not null references users(id),
    updated_at timestamptz not null default now()
);

alter table configuration_versions add column activated_by text references users(id);
alter table configuration_versions add column activated_at timestamptz;

create or replace function reject_configuration_version_mutation() returns trigger language plpgsql as $$
begin
    raise exception 'configuration versions are immutable';
end;
$$;

create trigger configuration_versions_no_update
before update or delete on configuration_versions
for each row execute function reject_configuration_version_mutation();

create table invoice_versions (
    id text primary key,
    contract_id text not null references contracts(id),
    version integer not null,
    configuration_version_id text not null references configuration_versions(id),
    state text not null default 'draft',
    unique(contract_id, version)
);

create table validation_runs (
    id text primary key,
    invoice_version_id text not null references invoice_versions(id),
    configuration_version_id text not null references configuration_versions(id),
    created_at timestamptz not null default now()
);
