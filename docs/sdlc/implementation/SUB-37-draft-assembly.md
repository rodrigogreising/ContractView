# SUB-37 Implementation Evidence: Evidence-Linked Draft Assembly

Status: Approved

## Scope

- Stable, idempotent invoice version assembled from the latest reconciled ledger and exact activated configuration.
- Each line retains expense key/date/vendor/description, mapped configured category, exact Decimal amount, ledger artifact and cell, supporting evidence artifact, extraction field/status, and mapping version.
- Reviewed extraction amount must match the ledger amount; unreviewed/mismatched/missing evidence and unmapped categories become visible findings.
- Invoice/category totals and configured remaining budget use exact Decimal arithmetic.
- Claimed-amount lineage links the imported source to the stable invoice version.

## Authority And State

- NGO Preparer alone assembles; server authorization precedes mutation.
- Repeating assembly for the same ledger/configuration returns the same invoice/version and creates no duplicate lines.
- Draft assembly does not attest, submit, or approve.

## Verification

- Five mapped lines total 10130.00.
- Category totals and available amounts match fixture expectations.
- Every complete-path line has ledger and supporting evidence links.
- EXP-003 uses reviewed 1280.00 and retains corrected extraction status.
- Missing evidence appears as an unresolved finding.
- Stable identifiers, idempotence, provenance, and role denial are proven.
- Focused draft integration suite: 2 passed.
- React suite: 4 passed; production TypeScript/Vite build passed.
- Authoritative clean full API suite: 57 passed.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Follow-up: SUB-40 formalizes deterministic rule runs; SUB-41 extends budget availability across invoice history.
- Advancement: SUB-37 and parent SUB-19 may move to Done; validation work may begin.
