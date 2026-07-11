alter table invoice_versions add column material_revision integer not null default 1;
alter table validation_runs add column material_revision integer;

create table attestations (
    id text primary key,
    invoice_version_id text not null references invoice_versions(id),
    validation_run_id text not null references validation_runs(id),
    material_revision integer not null,
    invoice_fingerprint text not null,
    actor_id text not null references users(id),
    actor_role text not null,
    attestation_version text not null,
    attestation_text text not null,
    created_at timestamptz not null default now()
);

create index attestations_invoice_idx on attestations(invoice_version_id,created_at desc);
create trigger attestations_no_update before update or delete on attestations
for each row execute function reject_provenance_mutation();
