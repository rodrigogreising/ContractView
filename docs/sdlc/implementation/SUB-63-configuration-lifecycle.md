# SUB-63 Governed Configuration Lifecycle Evidence

Status: Build

## Control

- Issue: `SUB-63` / REC-06
- Branch: `codex/sub-63-configuration-lifecycle`
- Base SHA: `be38a4a176dcca129bf053eebdc12dfc6d51be67`
- Project: ContractView / Build
- Generation skills: ADR/architecture, boundary, security/privacy,
  AI/config governance, requirements traceability, journey certification, and
  implementation/tests
- Required AI reviews: the matching seven review skills against an immutable
  base/head diff
- Human code review: not required. Runtime approval remains an explicit human
  Configuration Administrator action and is exercised through a normal session.

## Implemented Contract

The Configuration capability now implements:

`draft -> tested -> approved -> active -> superseded -> retired`

- A draft is mutable and never an active runtime input.
- Test creates an immutable numbered definition plus a deterministic
  `configuration-governance-v1` report, payload hash, and result hash.
- Approval records the canonical assigned human administrator, organization,
  role, test evidence, rationale, timestamp, and approval hash.
- Initial activation requires approval and no existing current active version.
- Supersession atomically replaces the current-active projection and appends
  predecessor `superseded` plus successor `active` events.
- Only a superseded version can retire.
- Rollback copies a superseded/retired definition into a new tested candidate;
  human approval and supersession remain mandatory.
- All runtime invoice/validation consumers resolve only the governed active
  projection and retain exact historical configuration foreign keys.

The API preserves existing paths where practical and adds explicit test,
approve, supersede, retire, rollback, and lifecycle-history endpoints. The
React administrator workspace exposes only valid state-specific actions,
requires a rationale, and renders retained evidence and relationship hashes.
The former direct activation control is removed.

## Persistence And Ownership

Migration `021_configuration_lifecycle.sql` adds four Configuration-owned
tables: immutable test evidence, immutable approvals, immutable lifecycle
events, and the current-active projection. Append-only triggers protect the
first three and the pre-existing immutable definition table. The statement
catalog contains 157 named statements and the ownership policy assigns 43
tables exactly once.

Lifecycle events also append versioned domain-event types:
`config_tested`, `config_approved`, `config_activated`, `config_superseded`,
`config_retired`, and `config_rollback_prepared`. Shared action and event
vocabularies generate matching Python and TypeScript consumers.

## Executable Acceptance Evidence

- Direct draft-to-active rejection with identical governance-table fingerprint.
- Complete two-version lifecycle plus retirement and a separately approved
  rollback candidate.
- Deterministic rollback payload and test-result hashes equal the retained
  target definition.
- Database-trigger evidence that definitions, test evidence, approvals, and
  lifecycle events cannot be deleted.
- Invalid-order, parallel activation, stale/foreign authority, and AI/system
  impersonation denial tests with zero partial mutation.
- Exact historical configuration foreign-key tests for invoices and validation.
- Normal server cookie session API test covering save, prohibited shortcut,
  test, approve, activate/supersede, history, logout, and post-logout denial.
- Frontend tests cover the bounded lifecycle/evidence surface and confirm the
  old direct activation label is absent.
- Clean synthetic reset with the worker stopped for deterministic ownership of
  queued jobs: 167 API tests pass. The worker is restarted for runtime health
  and background-processing checks.
- Frontend: 12 tests pass and the production TypeScript/Vite build succeeds.

The PR evidence manifest must add immutable base/head SHAs, exact commands,
exit codes, runtime versions, artifact hashes, AI review decisions, merge SHA,
and clean post-merge verification before Linear can move to Done.

## Risks And Dependencies

- This POC test suite requires deterministic reset before a complete run and a
  stopped worker during tests that explicitly claim queued jobs. REC-11 owns
  hermetic CI orchestration and durable manifest retention.
- Configuration test checks are deliberately bounded structural/deterministic
  POC checks, not production policy simulation or customer acceptance.
- Runtime configuration approval is performed by one synthetic seeded persona;
  production separation-of-duties, multi-party approval, revocation, and hosted
  audit controls remain out of scope and require a new governance review.
- REC-09, REC-10, and REC-12 remain blocked until this PR is merged and verified.
