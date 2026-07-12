# Synthetic Reimbursement Workflow POC

This repository contains a synthetic, vendor-neutral reimbursement-workflow
proof of concept. It demonstrates
configuration, evidence ingestion, deterministic validation, human authority,
immutable submission versions, return and resubmission, approval, and audit
reconstruction.

All organizations, people, transactions, documents, and credentials are test
fixtures. No real customer, employer, vendor, employee, account, or payment data
is permitted.

The application is demonstration software. It is not approved for real data,
hosted deployment, payment execution, or production reliance.

## Local Runtime

```bash
make prerequisites
make start
make reset
```

The web application is available at `http://localhost:4173` and the API at
`http://localhost:8000`.

The complete start/stop, migration, seed/reset, service, health, headless
certification, and paced headed recording commands are in the
[synthetic POC runbook](docs/operations/poc-runbook.md).

## Rights

See [LICENSE](LICENSE). Public visibility does not grant permission to use,
copy, modify, or redistribute the source.
