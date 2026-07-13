# SUB-75 Configuration Lifecycle And Provenance Evidence

Status: In Progress

Linear project stage: Build

Branch: `codex/sub-75-config-lifecycle-provenance`

Base SHA: `70099d0f23f89adeddb82fe6ffd3adedd4d8c8cd`

## Control And Scope

SUB-75 is the first implementation leaf after the merged SUB-74 design gate.
Merged prerequisites are SUB-17 `382876b7746e1147ee112e23bc80b95b90114d3a`,
SUB-56 `d8f99ebd27a5d3d99a6d1ad59477e94acd142ce3`, SUB-63
`a15d93637c0f998de5dc07374f6a6c975586f876`, and SUB-74
`70099d0f23f89adeddb82fe6ffd3adedd4d8c8cd`.

This leaf implements configuration lifecycle read models, optimistic draft
concurrency, current deterministic evidence verification, exact historical
runtime references, generated API/web contracts, and a bounded evidence panel.
It does not implement document profiles, cluster suggestions, profile fixture
evaluation, changed/unknown routing, the complete administrator workspace, or
terminal Journey 12 certification.

The declared scope is amended to include `services/api-workflow/app/manage.py`
for deterministic synthetic revision reset/fingerprinting and
`docs/architecture/module-ownership-policy.json` for the declared
Configuration read-model registration. Neither change creates production
bootstrap behavior or a new capability owner.

## Implementation

### Executable contracts and HTTP

`configuration-contracts` 1.2.0 adds typed DTOs for:

- editable configuration plus revision, payload hash, and update time;
- deterministic checks and immutable test evidence;
- human approval evidence bound to a test id;
- governed version detail with exact payload hash and lifecycle history;
- sorted human-readable diff and projection hash;
- prospective activation impact and reference counts; and
- exact invoice, validation, package, submission, snapshot, and audit-event
  references.

The canonical registry regenerates Pydantic and TypeScript consumers. Existing
paths remain stable; draft save and test add required expected-revision inputs,
and read-only version detail, compare, activation-impact, and references paths
are additive.

### Draft concurrency and lifecycle evidence

Migration 024 adds one positive revision to the Configuration-owned editable
draft. Save locks/reads the current draft, checks the expected revision, and
uses a compare-and-update statement. Test locks and compares the same revision
before freezing an immutable version. Concurrent/stale requests receive no
returned row and the transaction rolls back without governed mutation.

Approval recomputes and validates the exact deterministic report first.
Activation and supersession recompute the immutable payload hash, pinned
`configuration-governance-v1` report, result hash, successful result, exact
test id, and approval hash. State labels alone cannot promote a version. The
active record remains a prospective pointer and governed snapshots/events stay
append-only.

### Read-model and module boundary

Version detail is canonical Configuration data. Diff and activation impact are
pure sorted canonical-JSON projections with `canonical=false` and content
hashes. No projection table exists.

The configuration-to-runtime reference query is a named
`declared-read-model`. It reads stable ids from Invoices, Validation, Packages,
Workflow, and Provenance, declares every source owner, and is executable only
through the unit of work's read-model repository. It writes no table and is not
used by commands. Migration 024 adds only supporting indexes.

### Authorization and web projection

The server resolves contract ownership and explicit assignments from persisted
records. Full history/detail/diff/impact/references and all mutations require
the assigned Configuration Administrator. NGO and Government roles retain only
the existing scoped active summary; Auditor reconstruction remains the
submitted read-only audit projection.

The web app carries the server-issued draft revision, submits it on save/test,
consumes generated DTOs, and explains deterministic evidence, human approval,
diff, prospective impact, and historical references. The server remains the
authority. The existing Journey 11 save confirmation remains stable while the
revision is displayed in the evidence panel. SUB-77 owns the complete
profile-focused administrator workspace.

## Deterministic And Zero-Mutation Evidence

Focused tests prove:

- a successful save increments the draft revision exactly once;
- stale save and test leave draft fingerprints and governed version counts
  unchanged;
- failed deterministic evidence cannot activate even if a malformed approved
  lifecycle fixture is inserted;
- repeated diff/reference projection calls over unchanged immutable inputs
  return byte-equivalent values and equal projection hashes;
- successor activation leaves the prior configuration payload and its invoice,
  validation, package, submission, snapshot, and audit-event references intact;
- wrong-role and unassigned full-history/projection reads fail, while scoped
  NGO/Government active summaries remain read-only; and
- migration metadata contains the revision and four read-support indexes and
  no configuration projection table.

## Durable Evidence

- ADR: `docs/adr/0003-configurable-document-intake-mvp.md`
- Architecture/data flow: `docs/architecture/service-boundaries.md`,
  `docs/architecture/data-flow.md`, `docs/architecture/poc-boundary-review.md`,
  and `docs/architecture/module-ownership-policy.json`
- Security/privacy: `docs/sdlc/poc-security-privacy.md`
- AI/configuration governance: `docs/sdlc/poc-ai-governance.md`
- Requirements: `docs/sdlc/requirements-traceability.md`
- Journey checkpoint: `docs/journeys/12-configurable-document-intake-mvp.md`
- Executable tests: `services/api-workflow/tests/test_configuration.py`,
  `test_configuration_api.py`, `test_configuration_read_models.py`,
  `test_shared_contracts.py`, and web generated/component tests
- PR manifest: `tmp/evidence/SUB-75/pr/manifest.json` after immutable head exists

## Test Results

Recorded on 2026-07-13 before immutable PR review:

| Command | Exit | Result |
| --- | ---: | --- |
| `python3 scripts/check_persistence_statements.py` | 0 | 179 named statements; owner, consumer, collaboration kind, source tables, and generated ids pass |
| `python3 scripts/check_module_boundaries.py` | 0 | 47 table owners and 179 statements pass |
| `python3 scripts/check_shared_contracts.py` | 0 | Four registries and 43 contracts pass |
| pinned `bash scripts/ci/run_static.sh` | 0 | Python 3.12.2/Node 20.20.2; format, Ruff, mypy, contracts, persistence, boundaries, architecture, SDLC/recovery policies, 90 script tests, 24 frontend tests, production build, and web boundaries pass |
| focused Docker pytest after clean synthetic reset | 0 | 28 lifecycle, API, migration, authorization, provenance, replay, and shared-contract tests pass |
| full Docker API/workflow pytest after clean synthetic reset | 0 | 195 tests pass |
| `CI_PROJECT_NAME=contractview-sub75-final bash scripts/ci/run_hermetic.sh tmp/evidence/SUB-75/compose-final` | 0 | Two fresh PostgreSQL/MinIO passes over the frozen implementation; 195 tests per pass; API/web/worker health; equal reset fingerprint `cf0df3ccff130a8aefc15e30482e9a53ceb08b1c85aa8d3f65d1de0cb6bb35e8` |
| `JOURNEY11_PROJECT_NAME=contractview-sub75-fix-journey11 bash scripts/run_journey11.sh headless tmp/evidence/SUB-75/journey11-fix` | 0 | Canonical Journey 11 Playwright test passed after restoring the stable save confirmation; 1 test passed in 13.1 seconds |

Hosted run `29259147216` on the initial PR head caught the changed save
confirmation before merge. The stable Journey 11 text was restored without
removing the visible or typed revision. The hosted rerun and a fresh immutable
AI review over the corrected head remain pending.

## Review Plan

- Requirements traceability
- ADR/architecture
- Capability boundary
- Security/privacy
- AI/configuration governance
- Implementation/tests

No default human code-review approval is required. Approval depends on
executable evidence, hosted checks, and the six immutable AI review decisions,
followed by clean post-merge verification.
