# SUB-32 Implementation Evidence: Append-Only Events And Field Lineage

Status: Approved

## Scope

- Typed domain events for authentication, configuration activation, upload, extraction/failure, correction, validation, attestation, package generation, submission, return, revision, resubmission, and approval.
- Transaction-aware event writer so business commands append evidence in the same PostgreSQL transaction as canonical state.
- Field lineage records connecting value, source artifact/location, importer, provider/model, prompt/parser, mapping, correction actor/reason, rule run, invoice version, package artifact, and predecessor lineage.
- Authorized, ordered, read-only contract audit query intended for the SUB-50 UI.
- Authentication, configuration activation, and artifact registration already emit through the shared event contract.

## Immutability And Authority

- PostgreSQL triggers reject updates/deletes for domain events and field lineage.
- Projections may evolve separately; evidence records are append-only.
- Auditor is read-only across the synthetic scope; NGO access is organization-bound; Government access requires matching agency and submitted state.

## Verification

- Every canonical material event type appends and remains ordered.
- Login and logout create domain events.
- A field can be reconstructed from proposed extraction through human correction, rule run, invoice, and package.
- Direct event mutation fails.
- NGO, Government, Auditor, and cross-organization query boundaries behave correctly.
- Command: `docker compose run --rm api pytest -q`
- Result: 35 passed from a clean reset.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Follow-up: Each workflow story must append its typed event and lineage in the same transaction; SUB-50 renders this query.
- Advancement: SUB-32 may move to Done while the project remains in Build.
