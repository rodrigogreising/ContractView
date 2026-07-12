create table validation_input_manifests (
    id text primary key,
    invoice_snapshot_id text not null references invoice_snapshots(id),
    schema_version text not null,
    manifest jsonb not null,
    manifest_hash text not null unique check (manifest_hash ~ '^[a-f0-9]{64}$'),
    created_at timestamptz not null default now()
);

alter table validation_runs
add column input_manifest_id text references validation_input_manifests(id);

alter table validation_runs
add constraint validation_v2_requires_input_manifest
check (
    engine_version is null
    or engine_version <> 'deterministic-validation-v2'
    or input_manifest_id is not null
);

create table package_reproduction_manifests (
    id text primary key,
    package_id text not null unique references packages(id),
    validation_input_manifest_id text not null references validation_input_manifests(id),
    invoice_snapshot_id text not null references invoice_snapshots(id),
    template_id text not null,
    template_version integer not null check (template_version > 0),
    template_hash text not null check (template_hash ~ '^[a-f0-9]{64}$'),
    build_input jsonb not null,
    build_input_hash text not null check (build_input_hash ~ '^[a-f0-9]{64}$'),
    reproduction_manifest jsonb not null,
    reproduction_manifest_hash text not null check (
        reproduction_manifest_hash ~ '^[a-f0-9]{64}$'
    ),
    package_manifest_hash text not null check (package_manifest_hash ~ '^[a-f0-9]{64}$'),
    archive_sha256 text not null check (archive_sha256 ~ '^[a-f0-9]{64}$'),
    archive_byte_size bigint not null check (archive_byte_size >= 0),
    created_at timestamptz not null default now()
);

create trigger validation_input_manifests_no_update
before update or delete on validation_input_manifests
for each row execute function reject_provenance_mutation();

create trigger package_reproduction_manifests_no_update
before update or delete on package_reproduction_manifests
for each row execute function reject_provenance_mutation();

create index validation_input_manifests_snapshot_idx
on validation_input_manifests(invoice_snapshot_id, manifest_hash);

create index package_reproduction_validation_idx
on package_reproduction_manifests(validation_input_manifest_id, package_id);
