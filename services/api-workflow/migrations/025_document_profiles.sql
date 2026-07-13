alter table users
add constraint users_organization_key unique (id, organization_id);

create table document_profile_versions (
    id text primary key,
    contract_id text not null references contracts(id),
    profile_key text not null,
    version integer not null check (version >= 1),
    payload jsonb not null,
    content_hash text not null check (content_hash ~ '^[a-f0-9]{64}$'),
    predecessor_version_id text references document_profile_versions(id),
    created_by text not null references users(id),
    created_role text not null check (created_role = 'configuration_administrator'),
    created_organization_id text not null references organizations(id),
    created_at timestamptz not null default now(),
    unique (contract_id, profile_key, version),
    unique (id, contract_id),
    foreign key (contract_id, created_by, created_role)
        references contract_role_assignments(contract_id, user_id, role),
    foreign key (created_by, created_organization_id)
        references users(id, organization_id),
    foreign key (predecessor_version_id, contract_id)
        references document_profile_versions(id, contract_id)
);

create table document_profile_fixture_sets (
    id text primary key,
    profile_version_id text not null unique references document_profile_versions(id),
    contract_id text not null references contracts(id),
    version text not null,
    cases jsonb not null,
    content_hash text not null check (content_hash ~ '^[a-f0-9]{64}$'),
    created_by text not null references users(id),
    created_at timestamptz not null default now(),
    unique (id, profile_version_id),
    foreign key (profile_version_id, contract_id)
        references document_profile_versions(id, contract_id)
);

create table document_profile_evaluations (
    id text primary key,
    profile_version_id text not null unique references document_profile_versions(id),
    fixture_set_id text not null references document_profile_fixture_sets(id),
    contract_id text not null references contracts(id),
    suite_version text not null,
    ocr_version text not null,
    parser_version text not null,
    results jsonb not null,
    supported_field_exactness numeric(5,4) not null check (supported_field_exactness between 0 and 1),
    source_location_exactness numeric(5,4) not null check (source_location_exactness between 0 and 1),
    unknown_safe_routing_rate numeric(5,4) not null check (unknown_safe_routing_rate between 0 and 1),
    passed boolean not null,
    result_hash text not null check (result_hash ~ '^[a-f0-9]{64}$'),
    tested_by text not null references users(id),
    tested_role text not null check (tested_role = 'configuration_administrator'),
    tested_organization_id text not null references organizations(id),
    rationale text not null check (length(trim(rationale)) > 0),
    created_at timestamptz not null default now(),
    unique (id, profile_version_id),
    foreign key (profile_version_id, contract_id)
        references document_profile_versions(id, contract_id),
    foreign key (fixture_set_id, profile_version_id)
        references document_profile_fixture_sets(id, profile_version_id),
    foreign key (contract_id, tested_by, tested_role)
        references contract_role_assignments(contract_id, user_id, role),
    foreign key (tested_by, tested_organization_id)
        references users(id, organization_id)
);

create table document_profile_approvals (
    id text primary key,
    profile_version_id text not null unique references document_profile_versions(id),
    evaluation_id text not null references document_profile_evaluations(id),
    contract_id text not null references contracts(id),
    approved_by text not null references users(id),
    approved_role text not null check (approved_role = 'configuration_administrator'),
    approved_organization_id text not null references organizations(id),
    rationale text not null check (length(trim(rationale)) > 0),
    approval_hash text not null check (approval_hash ~ '^[a-f0-9]{64}$'),
    approved_at timestamptz not null default now(),
    foreign key (profile_version_id, contract_id)
        references document_profile_versions(id, contract_id),
    foreign key (evaluation_id, profile_version_id)
        references document_profile_evaluations(id, profile_version_id),
    foreign key (contract_id, approved_by, approved_role)
        references contract_role_assignments(contract_id, user_id, role),
    foreign key (approved_by, approved_organization_id)
        references users(id, organization_id)
);

create table document_profile_lifecycle_events (
    sequence bigserial primary key,
    id text not null unique,
    profile_version_id text not null references document_profile_versions(id),
    contract_id text not null references contracts(id),
    state text not null check (state in ('draft','tested','approved','active','superseded','retired')),
    action text not null check (action in ('create','test','approve_configuration','activate','rollback','supersede','retire')),
    actor_id text not null references users(id),
    actor_role text not null check (actor_role = 'configuration_administrator'),
    actor_organization_id text not null references organizations(id),
    rationale text not null check (length(trim(rationale)) > 0),
    evaluation_id text references document_profile_evaluations(id),
    approval_id text references document_profile_approvals(id),
    predecessor_version_id text references document_profile_versions(id),
    successor_version_id text references document_profile_versions(id),
    configuration_version_id text references configuration_versions(id),
    event_hash text not null check (event_hash ~ '^[a-f0-9]{64}$'),
    occurred_at timestamptz not null default now(),
    foreign key (profile_version_id, contract_id)
        references document_profile_versions(id, contract_id),
    foreign key (contract_id, actor_id, actor_role)
        references contract_role_assignments(contract_id, user_id, role),
    foreign key (actor_id, actor_organization_id)
        references users(id, organization_id),
    foreign key (predecessor_version_id, contract_id)
        references document_profile_versions(id, contract_id),
    foreign key (successor_version_id, contract_id)
        references document_profile_versions(id, contract_id)
);

create table document_profile_active_assignments (
    contract_id text not null references contracts(id),
    profile_key text not null,
    profile_version_id text not null unique references document_profile_versions(id),
    configuration_version_id text not null references configuration_versions(id),
    activated_by text not null references users(id),
    activated_role text not null check (activated_role = 'configuration_administrator'),
    activated_organization_id text not null references organizations(id),
    activated_at timestamptz not null default now(),
    primary key (contract_id, profile_key),
    foreign key (profile_version_id, contract_id)
        references document_profile_versions(id, contract_id),
    foreign key (configuration_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (contract_id, activated_by, activated_role)
        references contract_role_assignments(contract_id, user_id, role),
    foreign key (activated_by, activated_organization_id)
        references users(id, organization_id)
);

create table document_fingerprints (
    id text primary key,
    extraction_run_id text not null unique references extraction_runs(id),
    source_artifact_id text not null references artifacts(id),
    contract_id text not null references contracts(id),
    artifact_hash text not null check (artifact_hash ~ '^[a-f0-9]{64}$'),
    specification_version text not null,
    algorithm text not null check (algorithm = 'sha256-canonical-json-v1'),
    language_tag text not null,
    signals jsonb not null,
    fingerprint_sha256 text not null check (fingerprint_sha256 ~ '^[a-f0-9]{64}$'),
    ocr_version text not null,
    parser_version text not null,
    created_at timestamptz not null default now()
);

create table document_cluster_projections (
    id text primary key,
    contract_id text not null references contracts(id),
    fingerprint_id text not null unique references document_fingerprints(id),
    source_artifact_id text not null references artifacts(id),
    cluster_key text not null check (cluster_key ~ '^[a-f0-9]{64}$'),
    language_tag text not null,
    status text not null check (status = 'suggested'),
    canonical boolean not null check (canonical = false),
    projection_hash text not null check (projection_hash ~ '^[a-f0-9]{64}$'),
    created_at timestamptz not null default now()
);

create index document_cluster_projections_cluster_idx
on document_cluster_projections(contract_id, cluster_key, created_at);

create table document_profile_match_results (
    id text primary key,
    extraction_run_id text not null unique references extraction_runs(id),
    fingerprint_id text not null unique references document_fingerprints(id),
    contract_id text not null references contracts(id),
    outcome text not null check (outcome in ('recognized_profile_draft','needs_profile_review')),
    match_kind text not null check (match_kind in ('exact','none')),
    profile_version_id text references document_profile_versions(id),
    configuration_version_id text references configuration_versions(id),
    ledger_match_outcome text not null check (ledger_match_outcome in ('matched','unmatched','ambiguous','not_evaluated')),
    ledger_expense_key text,
    reason text not null,
    result_hash text not null check (result_hash ~ '^[a-f0-9]{64}$'),
    created_at timestamptz not null default now(),
    foreign key (profile_version_id, contract_id)
        references document_profile_versions(id, contract_id),
    foreign key (configuration_version_id, contract_id)
        references configuration_versions(id, contract_id)
);

create table document_profile_cluster_associations (
    id text primary key,
    contract_id text not null references contracts(id),
    cluster_key text not null check (cluster_key ~ '^[a-f0-9]{64}$'),
    profile_key text not null,
    status text not null check (status = 'draft'),
    confirmed_by text not null references users(id),
    confirmed_role text not null check (confirmed_role = 'configuration_administrator'),
    confirmed_organization_id text not null references organizations(id),
    rationale text not null check (length(trim(rationale)) > 0),
    association_hash text not null check (association_hash ~ '^[a-f0-9]{64}$'),
    created_at timestamptz not null default now(),
    unique (contract_id, cluster_key, profile_key),
    foreign key (contract_id, confirmed_by, confirmed_role)
        references contract_role_assignments(contract_id, user_id, role),
    foreign key (confirmed_by, confirmed_organization_id)
        references users(id, organization_id)
);

create or replace function reject_document_profile_evidence_mutation()
returns trigger language plpgsql as $$
begin
    raise exception 'document profile and intake evidence is immutable';
end;
$$;

create trigger document_profile_versions_no_mutation
before update or delete on document_profile_versions
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_profile_fixture_sets_no_mutation
before update or delete on document_profile_fixture_sets
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_profile_evaluations_no_mutation
before update or delete on document_profile_evaluations
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_profile_approvals_no_mutation
before update or delete on document_profile_approvals
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_profile_lifecycle_events_no_mutation
before update or delete on document_profile_lifecycle_events
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_profile_cluster_associations_no_mutation
before update or delete on document_profile_cluster_associations
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_fingerprints_no_mutation
before update or delete on document_fingerprints
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_cluster_projections_no_mutation
before update or delete on document_cluster_projections
for each row execute function reject_document_profile_evidence_mutation();

create trigger document_profile_match_results_no_mutation
before update or delete on document_profile_match_results
for each row execute function reject_document_profile_evidence_mutation();

alter table domain_events drop constraint domain_events_event_type_check;
alter table domain_events add constraint domain_events_event_type_check check (event_type in (
    'login_succeeded','login_failed','logout','config_tested','config_approved','config_activated',
    'config_superseded','config_retired','config_rollback_prepared','profile_drafted','profile_tested',
    'profile_approved','profile_activated','profile_rollback_activated','profile_superseded',
    'profile_retired','cluster_confirmed',
    'artifact_uploaded','document_routed','extraction_drafted','extraction_failed','field_corrected',
    'field_reviewed','validation_completed','invoice_line_corrected','finding_resolved','attested',
    'package_generated','submitted','returned','revision_created','resubmitted','approved'
));
