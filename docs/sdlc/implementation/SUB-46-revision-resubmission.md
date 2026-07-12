# SUB-46 Implementation Evidence: Returned Revision and Resubmission

Status: Implementation complete; immutable PR review pending

## Scope And Decision

SUB-46 implements the existing ADR 0001/0002 revision contract; it does not add
a new architecture decision or deployable. A structured Government return
atomically creates an editable successor linked to immutable v1 and its exact
decision. The NGO Preparer can correct only a persisted affected line named by
that decision. The server normalizes the expense key, corrected description,
and reason and appends the decision-bound correction event and lineage.

The UI displays the reason, note, immutable predecessor, editable successor,
and exact returned line set. It does not fall back to an arbitrary draft line
when feedback is incomplete. Server authorization remains controlling.

## Acceptance Evidence

- Return creates exactly one editable v2 with `corrects_return`, `returned_as`,
  and `amends` links to v1 and the Government decision.
- NGO Approver correction and Preparer correction of an unrelated existing line
  are denied. The latter compares material revision, line value, correction
  count, lineage count, and event count before/after for zero mutation.
- The accepted exact-line correction records normalized values, the Preparer,
  same-field predecessor lineage, and invoice/decision/entity references.
- V2 executes deterministic validation. A distinct NGO Approver re-attests,
  generates an immutable package, and resubmits through the normal commands.
- V1 package artifact rows and object bytes, hashes, validation findings,
  Government feedback, aggregate events, and invoice snapshots are captured
  after return and compared after final v2 approval.
- V2 retains validation/attestation/package/submission snapshots and distinct
  validation input, package build, package manifest, and archive identities.
- Frontend rendering tests cover the exact-line happy path and malformed
  feedback fail-closed behavior.

## Verification

Pre-commit implementation checks passed:

- repository static/architecture/SDLC suite: 71 tests, 106 typed Python files,
  four shared registries/27 contracts, six layers/nine capability owners, 47
  table owners, and 176 named persistence statements;
- frontend: 21 tests and production build passed using Node 20.20.2;
- clean runtime: two isolated PostgreSQL/MinIO Compose passes, 188 API tests per
  pass, API/web/worker health, and equal reset fingerprint
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`;
- focused behavior is part of the integrated API path and now asserts exact-line
  zero-mutation denial, normalized correction evidence, v1 byte/value equality,
  decision references, v2 deterministic validation, separate attestation,
  package/resubmission, and distinct reproducibility hashes.

The immutable base/head evidence manifest and AI review decisions are produced
after the issue branch is committed and the draft PR exists.

## Release Impact

Passing SUB-46 unblocks SUB-50. It does not certify the final Playwright journey,
public-source licensing, real-data use, staging, or production promotion.
