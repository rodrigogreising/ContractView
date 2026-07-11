alter table invoice_versions add column organization_id text references organizations(id);
alter table invoice_versions add column created_by text references users(id);
alter table invoice_versions add column total numeric(14,2);
alter table invoice_versions add column created_at timestamptz not null default now();

create table draft_assemblies (
    invoice_version_id text primary key references invoice_versions(id),
    ledger_import_id text not null references ledger_imports(id),
    configuration_version_id text not null references configuration_versions(id),
    created_at timestamptz not null default now(),
    unique(ledger_import_id, configuration_version_id)
);

create table invoice_lines (
    id text primary key,
    invoice_version_id text not null references invoice_versions(id),
    expense_row_id text not null references expense_rows(id),
    expense_key text not null,
    expense_date date not null,
    vendor text not null,
    description text not null,
    budget_category text not null,
    claimed_amount numeric(14,2) not null,
    ledger_artifact_id text not null references artifacts(id),
    ledger_source_location text not null,
    evidence_artifact_id text references artifacts(id),
    extraction_field_id text references extraction_fields(id),
    extraction_status text not null,
    mapping_version text not null,
    unique(invoice_version_id, expense_key)
);

create table invoice_findings (
    id text primary key,
    invoice_version_id text not null references invoice_versions(id),
    expense_key text,
    code text not null,
    message text not null,
    status text not null default 'open' check(status in ('open','resolved'))
);
