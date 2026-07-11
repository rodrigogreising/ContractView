alter table extraction_fields add column proposed_lineage_id bigint references field_lineage(id);
alter table extraction_fields add column reviewed_value text;
alter table extraction_fields add column reviewed_by text references users(id);
alter table extraction_fields add column reviewed_at timestamptz;

create table extraction_field_reviews (
    id text primary key,
    extraction_field_id text not null unique references extraction_fields(id),
    decision text not null check (decision in ('accept', 'correct')),
    proposed_value text not null,
    reviewed_value text not null,
    actor_id text not null references users(id),
    reason text,
    source_artifact_id text not null references artifacts(id),
    source_location text not null,
    predecessor_lineage_id bigint not null references field_lineage(id),
    reviewed_lineage_id bigint not null references field_lineage(id),
    created_at timestamptz not null default now()
);

create trigger extraction_field_reviews_no_update before update or delete on extraction_field_reviews
for each row execute function reject_provenance_mutation();

alter table domain_events drop constraint domain_events_event_type_check;
alter table domain_events add constraint domain_events_event_type_check check (event_type in (
    'login_succeeded','login_failed','logout','config_activated','artifact_uploaded',
    'extraction_drafted','extraction_failed','field_corrected','field_reviewed','validation_completed',
    'attested','package_generated','submitted','returned','revision_created','resubmitted','approved'
));
