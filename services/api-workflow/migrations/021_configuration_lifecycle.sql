alter table configuration_versions
drop constraint configuration_versions_status_check;

alter table configuration_versions
add constraint configuration_versions_status_check
check (status in ('draft', 'tested', 'approved', 'active', 'superseded', 'retired'));

alter table configuration_versions
add constraint configuration_versions_id_contract_unique unique (id, contract_id);

create table configuration_test_evidence (
    id text primary key,
    configuration_version_id text not null unique references configuration_versions(id),
    contract_id text not null references contracts(id),
    payload_hash text not null check (payload_hash ~ '^[a-f0-9]{64}$'),
    suite_version text not null,
    results jsonb not null,
    result_hash text not null check (result_hash ~ '^[a-f0-9]{64}$'),
    tested_by text not null references users(id),
    tested_role text not null check (tested_role = 'configuration_administrator'),
    tested_organization_id text not null references organizations(id),
    rationale text not null check (length(trim(rationale)) > 0),
    created_at timestamptz not null default now(),
    unique (id, configuration_version_id),
    foreign key (configuration_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (contract_id, tested_by, tested_role)
        references contract_role_assignments(contract_id, user_id, role)
);

create table configuration_approvals (
    id text primary key,
    configuration_version_id text not null unique references configuration_versions(id),
    contract_id text not null references contracts(id),
    test_evidence_id text not null references configuration_test_evidence(id),
    approved_by text not null references users(id),
    approved_role text not null check (approved_role = 'configuration_administrator'),
    approved_organization_id text not null references organizations(id),
    rationale text not null check (length(trim(rationale)) > 0),
    approval_hash text not null check (approval_hash ~ '^[a-f0-9]{64}$'),
    approved_at timestamptz not null default now(),
    foreign key (configuration_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (test_evidence_id, configuration_version_id)
        references configuration_test_evidence(id, configuration_version_id),
    foreign key (contract_id, approved_by, approved_role)
        references contract_role_assignments(contract_id, user_id, role)
);

create table configuration_lifecycle_events (
    sequence bigserial primary key,
    id text not null unique,
    configuration_version_id text not null references configuration_versions(id),
    contract_id text not null references contracts(id),
    state text not null check (state in ('tested', 'approved', 'active', 'superseded', 'retired')),
    action text not null check (action in ('test', 'approve_configuration', 'activate', 'supersede', 'retire', 'rollback')),
    actor_id text not null references users(id),
    actor_role text not null check (actor_role = 'configuration_administrator'),
    actor_organization_id text not null references organizations(id),
    rationale text not null check (length(trim(rationale)) > 0),
    test_evidence_id text references configuration_test_evidence(id),
    approval_id text references configuration_approvals(id),
    predecessor_version_id text references configuration_versions(id),
    successor_version_id text references configuration_versions(id),
    rollback_target_version_id text references configuration_versions(id),
    event_hash text not null check (event_hash ~ '^[a-f0-9]{64}$'),
    occurred_at timestamptz not null default now(),
    unique (configuration_version_id, state),
    foreign key (configuration_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (contract_id, actor_id, actor_role)
        references contract_role_assignments(contract_id, user_id, role),
    foreign key (predecessor_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (successor_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (rollback_target_version_id, contract_id)
        references configuration_versions(id, contract_id)
);

create index configuration_lifecycle_events_version_idx
on configuration_lifecycle_events(configuration_version_id, sequence desc);

create table configuration_active_versions (
    contract_id text primary key references contracts(id),
    configuration_version_id text not null unique references configuration_versions(id),
    activated_by text not null references users(id),
    activated_at timestamptz not null default now(),
    predecessor_version_id text references configuration_versions(id),
    rollback_target_version_id text references configuration_versions(id),
    foreign key (configuration_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (predecessor_version_id, contract_id)
        references configuration_versions(id, contract_id),
    foreign key (rollback_target_version_id, contract_id)
        references configuration_versions(id, contract_id)
);

create or replace function reject_configuration_governance_mutation()
returns trigger language plpgsql as $$
begin
    raise exception 'configuration governance evidence is immutable';
end;
$$;

create trigger configuration_test_evidence_no_mutation
before update or delete on configuration_test_evidence
for each row execute function reject_configuration_governance_mutation();

create trigger configuration_approvals_no_mutation
before update or delete on configuration_approvals
for each row execute function reject_configuration_governance_mutation();

create trigger configuration_lifecycle_events_no_mutation
before update or delete on configuration_lifecycle_events
for each row execute function reject_configuration_governance_mutation();

alter table domain_events drop constraint domain_events_event_type_check;
alter table domain_events add constraint domain_events_event_type_check check (event_type in (
    'login_succeeded','login_failed','logout','config_tested','config_approved','config_activated',
    'config_superseded','config_retired','config_rollback_prepared','artifact_uploaded',
    'extraction_drafted','extraction_failed','field_corrected','field_reviewed',
    'validation_completed','invoice_line_corrected','finding_resolved','attested',
    'package_generated','submitted','returned','revision_created','resubmitted','approved'
));
