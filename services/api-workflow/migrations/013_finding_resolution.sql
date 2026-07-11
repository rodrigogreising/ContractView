create table invoice_line_corrections (
    id text primary key,
    invoice_version_id text not null references invoice_versions(id),
    invoice_line_id text not null references invoice_lines(id),
    field_name text not null,
    prior_value text not null,
    corrected_value text not null,
    actor_id text not null references users(id),
    reason text not null,
    created_at timestamptz not null default now()
);

create table finding_resolutions (
    id text primary key,
    prior_finding_id text not null unique references validation_findings(id),
    invoice_version_id text not null references invoice_versions(id),
    action text not null check(action in ('correct','explain','dismiss')),
    actor_id text not null references users(id),
    reason text not null,
    new_validation_run_id text not null references validation_runs(id),
    created_at timestamptz not null default now()
);

create trigger invoice_line_corrections_no_update before update or delete on invoice_line_corrections
for each row execute function reject_provenance_mutation();
create trigger finding_resolutions_no_update before update or delete on finding_resolutions
for each row execute function reject_provenance_mutation();

alter table domain_events drop constraint domain_events_event_type_check;
alter table domain_events add constraint domain_events_event_type_check check (event_type in (
    'login_succeeded','login_failed','logout','config_activated','artifact_uploaded',
    'extraction_drafted','extraction_failed','field_corrected','field_reviewed','validation_completed',
    'invoice_line_corrected','finding_resolved','attested','package_generated','submitted','returned',
    'revision_created','resubmitted','approved'
));
