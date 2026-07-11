# SUB-46 Implementation Evidence: Returned Revision and Resubmission

Status: Approved

## Scope

- A structured return atomically creates an editable successor linked to immutable v1 and its decision.
- NGO Preparer sees exact reason/note/line feedback and may correct only the draft successor.
- Deterministic validation runs on v2; a distinct NGO Approver session must attest, generate, and submit v2.
- v1 package hashes, feedback, lines, and events remain immutable; v2 has its own manifest/PDF/ZIP and a distinct ZIP hash.

## Verification

- Clean full API regression: `70 passed`.
- Frontend suite: `9 passed`; production build passed.
- Integration test proves predecessor/successor link, preparer-only correction, v2 validation/re-attestation/package/resubmission, distinct hashes, unchanged v1 hash map/feedback, and final v2 state.

## Review Decision

Approved. Iteration creates a successor rather than modifying the submitted source-of-record version.
