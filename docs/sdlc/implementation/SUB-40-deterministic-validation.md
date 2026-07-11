# SUB-40 Implementation Evidence: Deterministic Validation

Status: Approved

## Rules

- `SERVICE_PERIOD` / `service-period-v1`.
- `REQUIRED_EVIDENCE` / `required-evidence-v1`.
- `BUDGET_AVAILABLE` / `budget-available-v1`.
- `TOTAL_RECONCILIATION` / `total-reconciliation-v1`.
- `POSSIBLE_DUPLICATE` / `possible-duplicate-v1`.

## Reproduction Contract

- Engine: `deterministic-validation-v1`.
- Input is normalized from one immutable invoice version and its exact configuration version.
- Canonical JSON input and sorted result arrays receive SHA-256 input/output hashes.
- Every result records rule/version, configured severity, reason, outcome, affected expense, normalized rule input, and explanation.
- Failed results create explicit findings; the full run and hashes are an append-only material event.

## Authority Boundary

- The validation module has no OCR, model, prompt, or extraction dependency.
- Only deterministic code creates results.
- NGO Preparer may run validation; other personas cannot create a run.

## Expected Fixture Findings

- Blocker: `SERVICE_PERIOD:EXP-004`.
- Warning: `POSSIBLE_DUPLICATE:EXP-005:EXP-002`.
- Evidence, configured budgets, and totals pass for the complete fixture.

## Verification And Review

- Focused deterministic suite: 4 passed.
- React suite: 6 passed; production TypeScript/Vite build passed.
- Authoritative clean full API suite: 62 passed.
- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Advancement: SUB-40 may move to Done; SUB-39 remains blocked only by SUB-41.
