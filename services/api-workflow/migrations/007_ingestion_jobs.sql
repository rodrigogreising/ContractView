create table ingestion_jobs (
    id text primary key,
    artifact_id text not null references artifacts(id),
    contract_id text not null references contracts(id),
    organization_id text not null references organizations(id),
    job_type text not null check (job_type in ('ledger_import', 'evidence_extract')),
    status text not null check (status in ('queued', 'running', 'completed', 'failed')),
    attempt_count integer not null default 0,
    error_code text,
    error_message text,
    created_by text not null references users(id),
    created_at timestamptz not null default now(),
    started_at timestamptz,
    completed_at timestamptz,
    unique(artifact_id, job_type)
);

create index ingestion_jobs_queue_idx on ingestion_jobs(status, created_at);
