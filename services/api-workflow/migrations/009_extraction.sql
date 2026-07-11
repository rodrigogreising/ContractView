alter table artifact_relations drop constraint artifact_relations_relation_type_check;
alter table artifact_relations add constraint artifact_relations_relation_type_check
check (relation_type in ('replaces', 'regenerates', 'derived_from'));

create table extraction_runs (
    id text primary key,
    job_id text not null unique references ingestion_jobs(id),
    source_artifact_id text not null references artifacts(id),
    raw_response_artifact_id text references artifacts(id),
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    provider text not null,
    model text not null,
    prompt_version text not null,
    parser_version text not null,
    schema_version text not null,
    source_location text not null,
    confidence numeric(5,4),
    status text not null check (status in ('needs_review', 'failed')),
    routing_reason text not null,
    error_message text,
    created_at timestamptz not null default now()
);

create table extraction_fields (
    id text primary key,
    extraction_run_id text not null references extraction_runs(id),
    field_name text not null,
    proposed_value text not null,
    confidence numeric(5,4) not null,
    source_location text not null,
    review_status text not null default 'proposed' check (review_status in ('proposed', 'accepted', 'corrected')),
    unique(extraction_run_id, field_name)
);
