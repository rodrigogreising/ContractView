# SUB-60 Tenant Authorization And Auditor Scoping Evidence

Status: Build / ready for immutable PR handoff after checks

## Control

- Issue: `SUB-60` / REC-04
- Branch: `codex/sub-60-tenant-authorization`
- Base SHA: `5894d61e9eafe176ec17459739ff3f1c10eeaa8c`
- Project: ContractView / Build
- Generation skills: `cv-generate-security-privacy`,
  `cv-generate-boundary-review`, `cv-generate-implementation-tests`
- Required AI reviews: `cv-review-security-privacy`,
  `cv-review-boundary-review`, `cv-review-implementation-tests`
- Human approval: not required; this synthetic code change performs no
  real-world governance acceptance or human-authority action.

## Implementation

- Added migration `019_contract_role_assignments.sql` with canonical agency,
  active-user, and role validation.
- Added deterministic synthetic administrator/auditor assignments to the
  fixture seed.
- Added a single canonical resolver for configuration, contract content,
  invoice, artifact, job, extraction, government decision, and audit scopes.
- Made caller-authored scopes fail closed.
- Restricted configuration administration to explicit contract assignment.
- Restricted auditors to assigned, submitted, read-only invoice, artifact,
  package, government-decision, and audit resources.
- Atomically published original ledger/evidence and linked extraction
  source/raw-response artifacts with the submitted invoice, including a
  numbered backfill migration for existing synthetic POC state.
- Filtered auditor event/lineage reconstruction so a submitted contract cannot
  disclose draft-only work.
- Derived government-decision publication from persisted returned/approved
  queue state instead of a caller or hard-coded flag.
- Routed every application authorization call through the canonical resolver;
  UI visibility remains non-authoritative.

## Acceptance Trace

| Acceptance criterion | Implementation and evidence |
| --- | --- |
| Canonical ownership, never caller ownership | `access_scope.py`; noncanonical all-role/action fail-closed test |
| Agency/contract-scoped configuration administrator | Assignment migration/seed; assigned and unassigned resolver tests |
| Explicit auditor assignment and submitted visibility | Auditor matrix, artifact lifecycle test, submitted-only audit filter test |
| Direct and indirect denial without mutation | Foreign contract, unassigned same-row update, and foreign artifact-reference tests with identical material-table content hashes and counts |
| Exhaustive role/org/resource coverage | Parameterized role, resource, submission, action, and tenant policy tests plus database integration tests |
| Security and boundary evidence | `docs/sdlc/poc-security-privacy.md` and `docs/architecture/poc-boundary-review.md` |
| AI review and merge verification | Pending immutable PR base/head review and clean post-merge verification |

## Changed Files And Ownership

- Identity/RBAC: `authorization.py`, `access_scope.py`, assignment migration,
  seed logic, fixture assignments.
- Capability callers: artifact, configuration, ingestion, extraction review,
  invoice, validation, findings, attestation, package, submission, government
  decision, revision, provenance, and budget application modules.
- Tests: policy matrix, canonical database scopes, no-mutation denials,
  auditor submitted visibility, configuration, artifact, extraction, fixture,
  and provenance regression expectations.
- Durable review evidence: this file, the security/privacy review, the boundary
  review, Linear handoff comments, and the machine-readable PR manifest.

## Executable Evidence

Clean synthetic database run on the rebuilt Python 3.12 API image:

```text
docker compose build api
docker compose run --rm api python -m app.manage reset
docker compose run --rm api pytest -q
150 passed in 8.49s
```

The focused authorization/security and submitted-workflow run passed 101 tests from a clean reset and
includes a 4,480-decision role/tenant/resource/action matrix. The complete
full API run supersedes it and includes all focused tests plus the full API
workflow regression.

Static checks:

```text
python3 -m compileall -q services/api-workflow/app services/api-workflow/tests
git diff --check
rg -n "ResourceScope\\(" services/api-workflow/app
```

The final search must return only the constructor inside `access_scope.py`.
Final exact command timestamps, environment versions, immutable base/head SHA,
artifact hashes, PR URL, and AI decisions are recorded in the machine-readable
evidence manifest at PR handoff.

## Determinism, Provenance, And Authority

- Authorization is a pure decision over canonical scope facts; database
  resolvers provide those facts before mutation.
- Denied commands do not call the mutation callback or the object store.
- Auditor reconstruction is a read-only declared projection over submitted
  canonical records and cannot mutate workflow state.
- AI extraction remains draft-only and has no role in authorization.
- NGO Approver and Government Reviewer authority is unchanged and remains
  server-enforced.

## Remaining Risks And Dependencies

- REC-07 must move resolver SQL into capability-owned persistence adapters; the
  current flat module is tested transitional code, not modular-monolith
  conformance.
- REC-08 must version authorization-relevant event payloads and finish immutable
  provenance relations.
- REC-11 must retain these checks and manifests in hermetic CI.
- REC-12 and Journey 11 remain required before release certification.
