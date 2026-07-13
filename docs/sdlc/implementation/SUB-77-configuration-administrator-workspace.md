# SUB-77 Configuration Administrator Workspace Evidence

Status: In Progress

Linear project stage: Build

Branch: `codex/sub-77-configuration-admin-workspace`

Base SHA: `7a8a1091443a012e5607451ded04be999933c5ef`

## Control And Scope

SUB-77 delivers the complete browser workspace over the merged configuration
and deterministic document-profile contracts. Its merged, post-merge-verified
prerequisites are SUB-17
`382876b7746e1147ee112e23bc80b95b90114d3a`, SUB-56
`d8f99ebd27a5d3d99a6d1ad59477e94acd142ce3`, SUB-65
`796f766fdaec7eedda4401b68537279f9bb9fa35`, SUB-75
`6d2437fa4d743ec470eac58692d0e4a0623b7736`, and SUB-76
`7a8a1091443a012e5607451ded04be999933c5ef`.

This leaf owns only the Configuration Administrator web projection and its
normal authenticated orchestration. It adds no persistence table, backend
authority, lifecycle transition, OCR/model behavior, or new domain contract.
SUB-78 remains responsible for the five-role Journey 12 and terminal release
certification.

## Workspace Behavior

The authenticated administrator sees three navigable, human-readable sections:

- Overview presents the current active control, editable draft revision,
  immutable history count, document-profile count, safe exception count,
  lifecycle vocabulary, prospective impact, and one derived next action.
- Configuration lifecycle edits governed business fields without exposing raw
  JSON, then displays immutable version history, detail, comparison, activation
  impact, runtime references, test evidence, approval, and lifecycle provenance.
- Profiles and exceptions creates an immutable profile draft from a governed
  fixture-backed template, exposes evaluation metrics and fixture results,
  preserves profile history, stages an exact profile reference into the
  editable configuration draft, and confirms a cluster suggestion only as a
  draft association.

Empty, loading, failure, unauthorized, inactive, and no-exception states are
explicit and accessible. The authenticated shell has a bounded wide layout;
browser certification asserts that the administrator page has no horizontal
viewport overflow.

## Authority And Governance

The browser never infers authority from button visibility. All data comes from
normal session-authenticated endpoints, and every command is re-authorized by
the existing Configuration owner. The client sends exact server ids, draft
revision, rationale, and typed command bodies; it cannot supply organization,
role, lifecycle state, approval, or activation evidence.

Activation is deliberately gated by successful immutable test evidence, a
recorded human approval, nonblank rationale, calculated future-only impact,
and an explicit impact-preservation checkbox. Profile fixture testing and
approval are separate actions. Selecting an approved profile only stages its
exact id/version/hash into the editable configuration draft; the normal
save/test/approve/activate lifecycle still applies. Confirming an unknown
cluster creates a named draft association and states that it is not active
configuration.

No AI behavior is added. Pinned local OCR output remains untrusted draft input;
fixture evaluation and all lifecycle gates remain deterministic. System and AI
actors retain no profile, configuration, validation, attestation, submission,
return, or approval authority.

## Boundary Decision

The Web feature consumes generated configuration DTOs and the typed read models
already returned by SUB-75/SUB-76. `features/configuration/api.ts` owns
transport calls; `App.tsx` owns session/contract-scoped orchestration;
`ConfigurationWorkspace` adapts the feature; and the configuration components
render state and emit commands. No feature component performs `fetch`, SQL,
cross-capability joins, or canonical computation.

Profile and cluster UI types are local read-model projections of existing
server payloads, not new canonical ontology. Server-owned configuration and
profile contracts remain the source of lifecycle vocabulary, exact version
references, evaluation evidence, and command validation.

## Test Evidence

Focused component tests prove:

- lifecycle states and next-action priority are distinguishable;
- activation remains disabled without successful evidence, human approval,
  rationale, and explicit prospective-impact confirmation;
- profile setup, evaluation, history, fixture outcomes, and safe exception
  states render without exposing private fixture transcripts; and
- governance failures use an accessible alert.

The canonical browser journey additionally proves a normal administrator
session, direct server denial of an invoice command, full configuration
activation, profile evaluation visibility, changed/unknown uploads, safe
cluster review, and draft-only confirmation. A viewport assertion and manual
browser inspection cover the responsive shell defect found during review.

## Durable Evidence

- ADR/design: `docs/adr/0003-configurable-document-intake-mvp.md`
- Architecture: `docs/architecture/service-boundaries.md` and
  `docs/architecture/poc-boundary-review.md`
- Security/privacy: `docs/sdlc/poc-security-privacy.md`
- AI/configuration governance: `docs/sdlc/poc-ai-governance.md`
- Requirements: `docs/sdlc/requirements-traceability.md`
- Journey checkpoint: `docs/journeys/12-configurable-document-intake-mvp.md`
- Frontend evidence: `ConfigurationAdmin.test.tsx`, `App.test.tsx`, and
  `tests/e2e/specs/journey11.spec.ts`
- PR manifest: `tmp/evidence/SUB-77/pr/manifest.json` after an immutable head
  exists

## Current Verification

| Command | Exit | Result |
| --- | ---: | --- |
| pinned `bash scripts/ci/run_static.sh` | 0 | Python 3.12.2/Node 20.20.2; format, Ruff, mypy, contract/persistence/boundary/policy checks, 90 script tests, 28 frontend tests, production build, and web boundaries pass |
| full clean Compose API/workflow suite | 0 | 217 tests pass, including configuration/profile lifecycle, authorization, deterministic routing, provenance, and immutable manifests |
| `JOURNEY11_PROJECT_NAME=contractview-sub77-final-profile bash scripts/run_journey11.sh headless tmp/evidence/SUB-77/journey-final-profile` | 0 | One clean canonical browser journey passes in 16.4 seconds with real configuration activation; profile successor create/test/approve/stage/save; changed/unknown routing; explicit impact confirmation; direct server denial; and draft-only cluster confirmation |
| `CI_PROJECT_NAME=contractview-sub77-final bash scripts/ci/run_hermetic.sh tmp/evidence/SUB-77/compose-final` | 0 | Two fresh PostgreSQL/MinIO passes run 217 tests each with equal reset fingerprint `98f77de03e5553b230c7956c0d8b8373b7ae12efd32c763a20deee8f3e7040fd` |
| in-app browser visual inspection at 1280 px | 0 | Overview, lifecycle, and profile/exception views have zero page overflow; profile cards have equal client/scroll widths after hash wrapping |

Hosted check, immutable AI reviews, merge, and post-merge verification are
recorded before Linear completion.

## Review Plan

- Requirements traceability
- Capability boundary
- Security/privacy
- AI/configuration governance
- Implementation/tests
- Journey checkpoint

No default human code-review approval is required. Approval depends on
executable evidence, hosted checks, immutable AI review decisions, and clean
post-merge verification.
