# SUB-41 Implementation Evidence: Budget Availability

Status: Approved

## Scope

- Shared exact-Decimal calculator for configured category and total requested, budgeted, remaining, and over-budget state.
- Snapshot is bound to the immutable configuration version referenced by the invoice, never a newer mutable draft.
- The deterministic `BUDGET_AVAILABLE` rule consumes this same calculator.
- NGO may read a draft snapshot; matching Government Reviewer may read after submission.

## Verification

- Fixture snapshot: requested 10130.00, budgeted 96000.00, remaining 85870.00.
- Category requested/budgeted/remaining values reconcile exactly.
- Property test proves requested + remaining = budgeted across cent values.
- 100.01 against 100.00 is over budget; corrected 100.00 passes.
- Government cannot read draft budget and can read the identical versioned snapshot after submission.
- Focused budget/validation suite: 8 passed.
- React suite: 6 passed; production TypeScript/Vite build passed.
- Authoritative clean full API suite: 66 passed.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Advancement: SUB-41 may move to Done and fully unblocks SUB-39.
