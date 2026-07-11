create table submissions (
  id text primary key,
  invoice_version_id text not null unique references invoice_versions(id),
  package_id text not null unique references packages(id),
  actor_id text not null references users(id),
  actor_role text not null,
  configuration_version_id text not null references configuration_versions(id),
  invoice_version integer not null,
  package_hashes jsonb not null,
  submitted_at timestamptz not null default now()
);
create table government_queue_items (
  id text primary key,
  submission_id text not null unique references submissions(id),
  agency_organization_id text not null references organizations(id),
  ngo_organization_id text not null references organizations(id),
  status text not null default 'submitted' check(status in ('submitted','returned','approved')),
  created_at timestamptz not null default now()
);
create trigger submissions_append_only before update or delete on submissions for each row execute function reject_provenance_mutation();

create or replace function reject_submitted_invoice_content_mutation() returns trigger language plpgsql as $$
begin
  if exists(select 1 from invoice_versions where id=old.invoice_version_id and state <> 'draft') then
    raise exception 'submitted invoice content is immutable';
  end if;
  return new;
end; $$;
create trigger invoice_lines_submitted_lock before update or delete on invoice_lines for each row execute function reject_submitted_invoice_content_mutation();

create or replace function allow_artifact_publication_only() returns trigger language plpgsql as $$
begin
  if tg_op='UPDATE' and old.submitted=false and new.submitted=true and (to_jsonb(old)-'submitted')=(to_jsonb(new)-'submitted') then return new; end if;
  raise exception 'artifact records are immutable';
end; $$;
drop trigger artifacts_no_update on artifacts;
create trigger artifacts_no_update before update or delete on artifacts for each row execute function allow_artifact_publication_only();
