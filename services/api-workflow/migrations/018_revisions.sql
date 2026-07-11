create table invoice_version_links (
  predecessor_invoice_version_id text not null unique references invoice_versions(id),
  successor_invoice_version_id text not null unique references invoice_versions(id),
  relation_type text not null default 'corrects_return',
  government_decision_id text not null unique references government_decisions(id),
  created_at timestamptz not null default now(),
  primary key(predecessor_invoice_version_id,successor_invoice_version_id)
);
create table revision_corrections (
  id text primary key,
  invoice_version_id text not null references invoice_versions(id),
  expense_key text not null,
  field_name text not null,
  prior_value text not null,
  corrected_value text not null,
  reason text not null,
  actor_id text not null references users(id),
  created_at timestamptz not null default now()
);
create trigger invoice_version_links_append_only before update or delete on invoice_version_links for each row execute function reject_provenance_mutation();
create trigger revision_corrections_append_only before update or delete on revision_corrections for each row execute function reject_provenance_mutation();
