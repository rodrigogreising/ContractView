# SUB-33 Implementation Evidence: Ledger Import

Status: Approved

## Scope

- CSV and XLSX parser for the synthetic expense-row-v1 schema.
- Canonical decimal expense rows with artifact, sheet, row, per-field cell coordinates, importer, schema, and mapping versions.
- Transactional field lineage for each material imported field.
- Exact Decimal reconciliation against the activated configuration's ledger control total.
- One import per immutable artifact; retries return the existing job/import and cannot duplicate expense rows.
- Malformed schema, invalid values, duplicate expense identifiers, and unreconciled totals fail the real job with no partial rows.

## Spreadsheet Verification

- Golden CSV and XLSX fixtures produce the same five canonical rows.
- Both reconcile exactly to 10130.00.
- Representative EXP-003 amount traces to CSV cell F4 and retains importer/schema/mapping versions.

## Verification

- Golden-format equivalence and exact total.
- Worker-backed persistence and completed job.
- Source row/cell and field-lineage evidence.
- Visible failure with transaction rollback for malformed/unreconciled input.
- Targeted ledger/worker suite: 15 passed.
- Authoritative clean full API suite: 50 passed.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Spreadsheet-skill influence: the styled XLSX table was inspected at its actual `June Ledger` sheet and row-4 header offset; its display labels are normalized through an explicit mapping while source coordinates retain the true workbook rows.
- Follow-up: SUB-37 consumes these canonical rows; SUB-40 consumes the retained exact configuration and lineage.
- Advancement: SUB-33 may move to Done while SUB-19 remains in Build.
