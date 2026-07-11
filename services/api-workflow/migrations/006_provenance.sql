create table domain_events (
    id bigserial primary key,
    event_type text not null check (event_type in (
        'login_succeeded','login_failed','logout','config_activated','artifact_uploaded',
        'extraction_drafted','extraction_failed','field_corrected','validation_completed',
        'attested','package_generated','submitted','returned','revision_created',
        'resubmitted','approved'
    )),
    actor_id text references users(id),
    organization_id text references organizations(id),
    contract_id text references contracts(id),
    aggregate_type text not null,
    aggregate_id text not null,
    payload jsonb not null default '{}'::jsonb,
    occurred_at timestamptz not null default now()
);

create index domain_events_contract_order_idx on domain_events(contract_id, id);
create index domain_events_organization_order_idx on domain_events(organization_id, id);

create table field_lineage (
    id bigserial primary key,
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    field_name text not null,
    field_value jsonb not null,
    source_artifact_id text references artifacts(id),
    source_location text,
    importer_version text,
    extractor_provider text,
    extractor_model text,
    prompt_version text,
    parser_version text,
    mapping_version text,
    correction_actor_id text references users(id),
    correction_reason text,
    validation_run_id text references validation_runs(id),
    invoice_version_id text references invoice_versions(id),
    package_artifact_id text references artifacts(id),
    predecessor_lineage_id bigint references field_lineage(id),
    recorded_at timestamptz not null default now()
);

create index field_lineage_contract_order_idx on field_lineage(contract_id, id);

create or replace function reject_provenance_mutation() returns trigger language plpgsql as $$
begin
    raise exception 'provenance records are append-only';
end;
$$;

create trigger domain_events_no_update before update or delete on domain_events
for each row execute function reject_provenance_mutation();

create trigger field_lineage_no_update before update or delete on field_lineage
for each row execute function reject_provenance_mutation();
