# SUB-38 Implementation Evidence: Bounded Configuration UI

Status: Approved

## Scope

- Configuration Administrator-only API and React form over the constrained configuration contract.
- Editable category limits, fixed five-rule enabled/severity settings and duplicate parameters, workflow labels, and package labels.
- Validated draft save, JSON preview, and activation of immutable numbered snapshots.
- Active configuration version badge available to NGO, Government, Auditor, and administrator screens without exposing mutation.

## Explicit Boundaries

- No rule expression language or general rule builder.
- No AI-authored configuration.
- Server-side role enforcement remains authoritative.
- Activated versions remain protected by the PostgreSQL immutability trigger established in SUB-30.

## Verification

- Admin edits settings, saves, previews, and activates a new numbered version.
- Later personas can read only the active id/version/timestamp.
- Non-admin draft reads/updates/activation fail.
- React renders all fixed configuration surfaces and active-version badge.
- Focused configuration suite: 6 passed.
- React suite: 5 passed; production TypeScript/Vite build passed.
- Authoritative clean full API suite: 58 passed.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Advancement: SUB-38 may move to Done and unblocks deterministic validation SUB-40.
