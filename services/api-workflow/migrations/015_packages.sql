create table packages (
  id text primary key,
  invoice_version_id text not null references invoice_versions(id),
  attestation_id text not null references attestations(id),
  version integer not null,
  zip_artifact_id text references artifacts(id),
  manifest jsonb not null,
  created_by text not null references users(id),
  created_at timestamptz not null default now(),
  unique(invoice_version_id, version)
);
create table package_artifacts (
  package_id text not null references packages(id),
  artifact_id text not null references artifacts(id),
  path text not null,
  sha256 text not null,
  primary key(package_id, path),
  unique(artifact_id)
);
create trigger packages_append_only before update or delete on packages for each row execute function reject_provenance_mutation();
create trigger package_artifacts_append_only before update or delete on package_artifacts for each row execute function reject_provenance_mutation();
