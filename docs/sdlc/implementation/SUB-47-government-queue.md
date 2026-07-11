# SUB-47 Implementation Evidence: Government Review Queue

Status: Approved

## Scope

- Agency-scoped server query lists submitted versions with status, NGO, contract, service period, amount, findings, submission time, and exact package reference.
- Exact review context exposes immutable artifact paths/hashes/downloads, latest deterministic validation, findings, configuration version, and provenance summary.
- Only the seeded Government Reviewer may query this surface; NGO personas are denied and receive no government-only UI.
- Return and approve controls are isolated to the Government Reviewer workspace; their command behavior is implemented by SUB-49.

## Verification

- Focused backend workflow suite: `9 passed`.
- Frontend suite: `9 passed`; production build passed.
- Tests prove NGO denial without mutation, agency scoping, correct queue fields, exact ZIP linkage, validation/finding context, and submitted provenance.

## Review Decision

Approved. Read models remain scoped to immutable submitted records and do not grant any NGO persona government controls.
