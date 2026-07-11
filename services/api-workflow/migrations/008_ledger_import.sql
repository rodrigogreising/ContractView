create table ledger_imports (
    id text primary key,
    job_id text not null unique references ingestion_jobs(id),
    artifact_id text not null unique references artifacts(id),
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    source_sheet text not null,
    importer_version text not null,
    schema_version text not null,
    mapping_version text not null,
    control_total numeric(14,2) not null,
    imported_total numeric(14,2) not null,
    row_count integer not null,
    created_at timestamptz not null default now()
);

create table expense_rows (
    id text primary key,
    ledger_import_id text not null references ledger_imports(id),
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    expense_key text not null,
    expense_date date not null,
    vendor text not null,
    description text not null,
    budget_category text not null,
    amount numeric(14,2) not null,
    invoice_number text not null,
    evidence_filename text not null,
    source_artifact_id text not null references artifacts(id),
    source_sheet text not null,
    source_row integer not null,
    source_cells jsonb not null,
    importer_version text not null,
    schema_version text not null,
    mapping_version text not null,
    unique(ledger_import_id, expense_key),
    unique(source_artifact_id, source_sheet, source_row)
);
