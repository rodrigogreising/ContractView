# Synthetic Reimbursement Workflow POC

This repository is the private engineering source for a synthetic,
vendor-neutral reimbursement-workflow proof of concept. It demonstrates
configuration, evidence ingestion, deterministic validation, human authority,
immutable submission versions, return and resubmission, approval, and audit
reconstruction.

All organizations, people, transactions, documents, and credentials are test
fixtures. No real customer, employer, vendor, employee, account, or payment data
is permitted.

## Public Candidate

Public disclosure is produced through the deterministic publication builder,
not by changing this repository's visibility. The builder creates a standalone
neutral snapshot without Git history, internal implementation evidence, PR
metadata, or private control-plane references. Publication still requires an
explicit owner decision.

## Local Runtime

```bash
docker compose up --build
docker compose exec api python -m app.manage reset
```

The web application is available at `http://localhost:4173` and the API at
`http://localhost:8000`.

## Rights

See [LICENSE](LICENSE). Public visibility does not grant permission to use,
copy, modify, or redistribute the source.
