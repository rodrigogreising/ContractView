# SUB-68 Reproducible Validation And Packages

Status: Build

## Control

- Issue: `SUB-68` / REC-09
- Branch: `codex/sub-68-reproducible-validation-packages`
- Base SHA: `1a62ce922091a863863b2030a0f6773a87ecef1e`
- Project: ContractView / Build
- Merged prerequisites: SUB-58 `08ae4ffef3f2ef386473149b596b6a5abbc147d8`;
  SUB-62 `be38a4a176dcca129bf053eebdc12dfc6d51be67`;
  SUB-63 `a15d93637c0f998de5dc07374f6a6c975586f876`;
  SUB-64 `45964570a986f7f87b772ba73d46b17c233c915e`
- Human code review: not required. Executable evidence and applicable
  immutable-diff AI reviews are the code gate.

## Implemented Contract

Shared configuration contracts now define extraction-component references,
validation input manifests, package build inputs, file digests, and package
reproduction manifests. Shared rule contracts bind validation runs to exact
input manifest identifiers/hashes. Generated Python and TypeScript consumers
are checked for drift and compatibility.

Validation captures an immutable invoice snapshot, resolves exact source
artifact and configuration/schema/mapping/rule/workflow/view/template and
extraction versions, validates shared rule definitions, and persists a
content-addressed input manifest before storing results. A replay loads that
manifest and snapshot, re-executes the same rules, and compares the canonical
result hash without consulting mutable current state.

Package generation captures a package-stage snapshot and versioned template
contract. It stores the exact build input, deterministic generated-file
digests, final archive hash, and reproduction result. ZIP metadata and file
order are fixed. Replay verifies retained object hashes, renders from the exact
contract, and compares every file and the archive byte-for-byte.

Migration `023_reproducibility_manifests.sql` adds capability-owned append-only
manifest tables and requires every v2 validation run to reference its input.
The physical policy covers 47 owned tables and 173 named statements.

## Defect Found During Certification

The first clean two-pass run found a real replay mismatch: `manifest.csv` was
generated from dictionary insertion order, while PostgreSQL JSONB returns keys
in canonicalized order. Live generation and persisted replay therefore emitted
different CSV columns and package bytes. The fix defines `CLAIM_COLUMNS`
explicitly, includes it in the versioned template parameters/hash, and uses it
for all CSV generation. The certification test now proves in-memory generation
and JSONB-backed replay are byte-identical.

## Executable Acceptance Evidence

- Shared contract validation: 4 registries and 26 contracts pass generation,
  compatibility, drift, and consumer checks.
- Persistence/module policy: 47 table owners and 173 named statements pass
  capability ownership, read-model, and forbidden-boundary checks.
- API suite: 179 tests pass from each of two independently created clean
  PostgreSQL/MinIO environments.
- Both independent runs produce semantic fingerprint
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- Validation tests prove exact manifest contents, deduplication, append-only
  behavior, shared-rule execution, and identical replay results.
- Package tests prove deterministic PDF/JSON/CSV/ZIP output, exact manifest
  and object-store integrity checks, unchanged V1, distinct V2 hashes, and
  Auditor reconstruction.
- Changed invoice/configuration/template/extraction inputs are represented by
  new content identities rather than overwriting retained execution evidence.

## Required Immutable AI Review

Run ADR/architecture, boundary, AI governance, security/privacy, requirements
traceability, implementation/tests, Journey 11, and release-readiness reviews
against the immutable PR base/head diff. Review may not mutate the diff. Any
required fix becomes another commit and repeats CI and review.

## Completion Conditions

Before Done, retain the hosted CI evidence manifest with exact base/head SHAs,
commands, versions, counts, hashes, and prerequisite merge proof; record the AI
review decisions; merge the PR; and pass clean post-merge certification at the
merge SHA. SUB-65, SUB-66, REC-12, and SUB-55 remain dependent on merged and
verified evidence rather than issue status alone.
