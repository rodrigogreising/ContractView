alter table validation_runs add column engine_version text;
alter table validation_runs add column normalized_inputs jsonb;
alter table validation_runs add column input_hash text;
alter table validation_runs add column output_hash text;
alter table validation_runs add column created_by text references users(id);
alter table validation_runs add column status text default 'completed';

create table validation_results (
    id text primary key,
    validation_run_id text not null references validation_runs(id),
    rule_code text not null,
    rule_version text not null,
    severity text not null check(severity in ('blocker','warning')),
    reason_code text not null,
    outcome text not null check(outcome in ('pass','fail')),
    expense_key text,
    normalized_input jsonb not null,
    message text not null
);

create table validation_findings (
    id text primary key,
    validation_result_id text not null references validation_results(id),
    invoice_version_id text not null references invoice_versions(id),
    validation_run_id text not null references validation_runs(id),
    expense_key text,
    code text not null,
    severity text not null check(severity in ('blocker','warning')),
    message text not null,
    status text not null default 'open' check(status in ('open','resolved','dismissed'))
);

create index validation_results_run_idx on validation_results(validation_run_id,rule_code,expense_key);
create index validation_findings_invoice_idx on validation_findings(invoice_version_id,status,severity);
