# SUB-50 Implementation Evidence: Read-Only Audit Timeline

Status: Implementation complete; immutable PR review pending

## Scope And Decision

SUB-50 exposes append-only provenance, immutable invoice snapshots, and package
reproduction manifests as a typed read projection. It adds no deployable,
table, write path, or AI authority. `event-contracts` 1.1.0 owns generated
Python/TypeScript audit DTOs; Provenance assembles the projection; HTTP and
React consume that contract without inventing a parallel client ontology.

Auditor scope is resolved from canonical contract assignment and submitted
invoice state. The endpoint is GET-only. The workspace contains no form or
mutation control, and direct Auditor mutation requests are denied without
changes to configuration, artifact, invoice, validation, attestation, package,
submission, or decision state.

## Acceptance Evidence

- The ordered material-event timeline includes configuration activation,
  source upload, extraction, human correction, deterministic validation,
  finding resolution, attestation, package generation, initial submission,
  Government return, revision, correction, resubmission, and approval.
- Canonical event, relation, correction, and snapshot actors retain user,
  organization, role, timestamp, version references, and content hashes.
- `field_corrected` and `resubmitted` are emitted as their closed ontology
  values instead of being collapsed into `field_reviewed` and `submitted`.
- Every package claim produces an explicit source artifact/location → validation
  run → invoice snapshot/version → package trail. The complete journey proves
  the returned expense traverses both immutable packages with distinct archive
  hashes while v1 remains byte- and hash-stable.
- The UI renders exact actor, version, source, validation, template, manifest,
  reproduction, and archive evidence. The server remains authoritative.

## Verification

- Static/architecture/SDLC gate: 71 repository tests, 106 typed Python files,
  four registries/34 contracts, six layers/nine capability owners, 47 table
  owners, and 177 named statements.
- Frontend: 22 tests and production build with Node 20.20.2.
- Clean runtime: two isolated PostgreSQL/MinIO Compose passes, 189 API tests per
  pass, API/web/worker health, and identical semantic fingerprint
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- Focused assertions cover the complete material event set, exact actors, all
  eight relation types, immutable snapshots, both package manifests, explicit
  claimed-amount trails, two distinct hashes, GET authorization, and
  zero-mutation HTTP denials.

Immutable base/head evidence and AI review decisions are produced only after
the issue commit and draft PR exist.

## Release Impact

Passing SUB-50 unblocks SUB-55's audit segment. It does not itself certify the
Playwright recording harness, paced demo artifacts, or final release decision.
