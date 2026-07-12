# SUB-64 Provenance And Immutable Snapshot Evidence

Status: Build

## Control

- Issue: `SUB-64` / REC-08
- Branch: `codex/sub-64-provenance-snapshots`
- Base SHA: `a15d93637c0f998de5dc07374f6a6c975586f876`
- Project: ContractView / Build
- Generation and required immutable-diff AI review skills: ADR/architecture,
  boundary, security/privacy, AI governance, requirements traceability,
  Journey 11 certification, and implementation/tests
- Human code review: not required. NGO attestation and government decisions
  remain normal-session human runtime authority actions.

## Implemented Contract

Migration `022_provenance_snapshots.sql` adds required versioned material-event
fields, typed append-only relations, and immutable invoice snapshots for
validation, attestation, package, and submission stages. Each downstream record
retains the exact snapshot foreign key. Event and relation hashes cover their
canonical semantic documents; snapshot hashes cover exact line data, source
artifact hashes, configuration, invoice version, material revision, state, and
mapping versions.

The application derives actor role and actor organization from the canonical
identity record while retaining resource organization separately. The shared
ontology validates version references and relation types. Auditor read models
derive visibility from canonical invoice state and expose versioned events,
relations, snapshots, and field lineage without mutation authority.

Return creates a new invoice aggregate, clones v1 lineage into v2 with explicit
predecessor edges, and records `returned_as` plus `amends`. Revision correction
appends a same-field successor. The expense-date finding correction now selects
an `expenseDate` predecessor rather than the former `claimedAmount` edge.

## Executable Acceptance Evidence

- Clean synthetic migration/reset and focused API run: 15 tests pass.
- Clean full API regression after targeted additions: 175 tests pass.
- Persistence policy: 45 table owners and 167 named statements pass ownership,
  consumer, operation, and declared-read-model validation.
- Material envelopes expose schema, canonical actor/role/organizations,
  resource scope, immutable references, and 64-character hashes; a raw
  incomplete insert is rejected by PostgreSQL.
- Actual Journey 11 command flow records all eight relation types:
  `supports`, `derived_from`, `maps_to`, `validated_by`, `submitted_as`,
  `returned_as`, `amends`, and `approved_as`.
- Auditor-visible event and relation documents independently recompute to their
  retained SHA-256 hashes, including actor organization and exact references.
- Validation, attestation, package, and submission records point to exact stage
  snapshots; each retained hash recomputes from the canonical payload.
- Database triggers reject snapshot/event/relation/validation mutation.
- Expense-date correction links to the same field. V2 description lineage links
  v1 mapping -> v2 clone -> v2 human correction.
- After final v2 approval, v1 snapshot rows and package hashes are byte-for-byte
  unchanged, v2 has its own complete snapshot set, and the Auditor reconstructs
  both versions and the approval relation.
- Frontend: 13 tests pass and the production build succeeds. Full Compose smoke
  reaches healthy PostgreSQL, MinIO, API, worker, and web services with real
  readiness endpoints responsive.

## Remaining Handoff Evidence

Before Done, the PR manifest must record immutable base/head SHAs, exact clean
commands, exit codes, tool/runtime versions, artifact hashes, seven AI review
decisions, merge SHA, and clean post-merge verification. REC-09 consumes these
snapshots and version references for reproducible validation/package manifests;
REC-12 remains blocked until this PR and the other recovery leaves are merged.
