# SUB-39 Implementation Evidence: Finding Resolution

Status: Approved

## Scope

- Latest validation findings show reason code, severity, affected expense, normalized rule input, linked evidence, explanation, and remediation.
- NGO Preparer may correct the supported service-period blocker or explain/dismiss configured warnings.
- Canonical correction changes EXP-004 service date through an append-only line-correction record, event, and lineage, then creates a new deterministic validation run.
- Warning resolution retains the failing deterministic result while marking the finding projection dismissed with an explicit explanation and new run.
- Resolution history records prior finding, action, actor, reason, time, and new validation run.

## Approval Gate

- `has_open_blockers()` returns true when no completed run exists or the latest run has an open blocker.
- SUB-43 must call this server-side before attestation; UI visibility is not sufficient.

## Verification

- EXP-004 correction removes the blocker in a new run without deleting the prior finding.
- Duplicate warning is explained/dismissed while its rule result remains historical.
- Actor/reason/prior finding/new run/correction lineage/events are present.
- Approver and cross-organization resolution attempts create no mutation.
- Open blocker gate transitions from true to false only after correction.
- Focused validation/resolution suite: 6 passed.
- React suite: 7 passed; production TypeScript/Vite build passed.
- Authoritative clean full API suite: 67 passed.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Advancement: SUB-39 and validation parent SUB-20 may move to Done; NGO approval work can begin.
