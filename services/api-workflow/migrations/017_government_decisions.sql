create table government_decisions (
  id text primary key,
  queue_item_id text not null references government_queue_items(id),
  submission_id text not null references submissions(id),
  invoice_version_id text not null references invoice_versions(id),
  package_id text not null references packages(id),
  decision text not null check(decision in ('returned','approved')),
  reason_code text not null,
  note text not null,
  line_keys jsonb not null default '[]',
  actor_id text not null references users(id),
  actor_role text not null,
  decided_at timestamptz not null default now(),
  unique(queue_item_id,decision)
);
create trigger government_decisions_append_only before update or delete on government_decisions for each row execute function reject_provenance_mutation();
