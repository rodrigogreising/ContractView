-- Optimistic concurrency belongs to the editable draft. Immutable governed
-- versions and their evidence remain append-only.
alter table configuration_drafts
add column revision bigint not null default 1 check (revision > 0);

-- These indexes support derived, noncanonical configuration provenance and
-- activation-impact projections. They add no mutable projection state.
create index invoice_versions_configuration_reference_idx
on invoice_versions(configuration_version_id, created_at, id);

create index validation_runs_configuration_reference_idx
on validation_runs(configuration_version_id, created_at, id);

create index submissions_configuration_reference_idx
on submissions(configuration_version_id, submitted_at, id);

create index domain_events_version_references_idx
on domain_events using gin(version_references jsonb_path_ops);
