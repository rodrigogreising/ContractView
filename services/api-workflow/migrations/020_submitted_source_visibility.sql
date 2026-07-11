update artifacts a set submitted=true
where a.submitted=false and a.id in (
    select l.ledger_artifact_id
    from invoice_lines l
    join invoice_versions i on i.id=l.invoice_version_id
    where i.state<>'draft'
    union
    select l.evidence_artifact_id
    from invoice_lines l
    join invoice_versions i on i.id=l.invoice_version_id
    where i.state<>'draft' and l.evidence_artifact_id is not null
    union
    select x.source_artifact_id
    from invoice_lines l
    join invoice_versions i on i.id=l.invoice_version_id
    join extraction_fields f on f.id=l.extraction_field_id
    join extraction_runs x on x.id=f.extraction_run_id
    where i.state<>'draft'
    union
    select x.raw_response_artifact_id
    from invoice_lines l
    join invoice_versions i on i.id=l.invoice_version_id
    join extraction_fields f on f.id=l.extraction_field_id
    join extraction_runs x on x.id=f.extraction_run_id
    where i.state<>'draft' and x.raw_response_artifact_id is not null
);
