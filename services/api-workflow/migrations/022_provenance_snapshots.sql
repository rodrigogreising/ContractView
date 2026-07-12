alter table domain_events
add column event_key text unique,
add column schema_version integer not null default 1 check (schema_version > 0),
add column actor_role text,
add column actor_organization_id text references organizations(id),
add column reason_code text,
add column version_references jsonb not null default '[]'::jsonb
    check (jsonb_typeof(version_references) = 'array'),
add column event_hash text check (event_hash is null or event_hash ~ '^[a-f0-9]{64}$');

create or replace function require_versioned_material_event()
returns trigger language plpgsql as $$
begin
    if new.event_type not in ('login_succeeded','login_failed','logout') and (
        new.event_key is null or new.actor_id is null or new.actor_role is null
        or new.actor_organization_id is null or new.organization_id is null
        or new.contract_id is null or new.event_hash is null
        or jsonb_array_length(new.version_references) = 0
    ) then
        raise exception 'material events require actor, role, organizations, contract, hash, and version references';
    end if;
    return new;
end;
$$;

create trigger domain_events_require_versioned_material_event
before insert on domain_events
for each row execute function require_versioned_material_event();

create table provenance_relations (
    id text primary key,
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    relation_type text not null check (relation_type in (
        'supports','derived_from','maps_to','validated_by','submitted_as',
        'returned_as','amends','approved_as'
    )),
    source_reference jsonb not null,
    target_reference jsonb not null,
    schema_version integer not null default 1 check (schema_version > 0),
    actor_id text not null references users(id),
    actor_role text not null,
    actor_organization_id text not null references organizations(id),
    reason_code text,
    relation_hash text not null check (relation_hash ~ '^[a-f0-9]{64}$'),
    created_at timestamptz not null default now(),
    unique (relation_type, source_reference, target_reference)
);

create index provenance_relations_contract_order_idx
on provenance_relations(contract_id, created_at, id);

create table invoice_snapshots (
    id text primary key,
    invoice_version_id text not null references invoice_versions(id),
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    invoice_version integer not null check (invoice_version > 0),
    material_revision integer not null check (material_revision > 0),
    stage text not null check (stage in (
        'validation','attestation','package','submission'
    )),
    payload jsonb not null,
    snapshot_hash text not null check (snapshot_hash ~ '^[a-f0-9]{64}$'),
    created_by text not null references users(id),
    actor_role text not null,
    created_at timestamptz not null default now(),
    unique (invoice_version_id, material_revision, stage)
);

alter table validation_runs
add column invoice_snapshot_id text references invoice_snapshots(id);

alter table attestations
add column invoice_snapshot_id text references invoice_snapshots(id);

alter table packages
add column invoice_snapshot_id text references invoice_snapshots(id);

alter table submissions
add column invoice_snapshot_id text references invoice_snapshots(id);

create trigger provenance_relations_no_update
before update or delete on provenance_relations
for each row execute function reject_provenance_mutation();

create trigger invoice_snapshots_no_update
before update or delete on invoice_snapshots
for each row execute function reject_provenance_mutation();

create trigger validation_runs_no_update
before update or delete on validation_runs
for each row execute function reject_provenance_mutation();

create trigger validation_results_no_update
before update or delete on validation_results
for each row execute function reject_provenance_mutation();
