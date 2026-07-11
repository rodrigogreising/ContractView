# SUB-49 Implementation Evidence: Government Return and Final Approval

Status: Approved

## Scope

- Government Reviewer returns the exact submitted v1 with a supported reason, required note, and affected expense keys.
- Append-only decisions bind queue, submission, invoice, package, actor, role, time, reason, note, and lines.
- State-machine guards reject unauthorized, stale, duplicate, and out-of-order actions.
- Approval requires a later submitted version and a prior return for the same contract.
- The actor must match a provisioned seeded human reviewer; fabricated system/AI actors are rejected.

## Verification

- Clean full API regression: `70 passed`.
- Frontend suite: `9 passed`; production build passed.
- Integration test covers NGO denial, system/AI exclusion, stale action rejection, v1 return, v2-only approval, and durable decision/event fields.

## Review Decision

Approved. Return and approval remain explicit human-authority commands with no AI or system decision path.
