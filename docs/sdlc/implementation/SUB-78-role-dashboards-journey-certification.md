# SUB-78 Role Dashboards And Journey 12 Certification

Status: In Review — candidate implementation and local evidence complete;
immutable PR reviews, exact-head hosted certification, merge, and post-merge
verification remain required

Linear project stage: Evidence Review

Branch: `codex/sub-78-role-dashboards-journey-certification`

Base SHA: `2203689460a3d8b8f46525a0c45a30d50f44c009`

## Control And Scope

SUB-78 is the terminal leaf of MVP epic SUB-73. Its six prerequisites are
merged and post-merge verified: SUB-17
`382876b7746e1147ee112e23bc80b95b90114d3a`, SUB-56
`d8f99ebd27a5d3d99a6d1ad59477e94acd142ce3`, SUB-65
`796f766fdaec7eedda4401b68537279f9bb9fa35`, SUB-67
`1a62ce922091a863863b2030a0f6773a87ecef1e`, SUB-76
`7a8a1091443a012e5607451ded04be999933c5ef`, and SUB-77
`2203689460a3d8b8f46525a0c45a30d50f44c009`.

The leaf owns useful NGO Preparer, NGO Approver, Government Reviewer, and
Auditor landing pages plus terminal Journey 12/release evidence. It does not
add a capability owner, table, migration, deployable, provider, runtime AI, or
new authority. ADR 0003 already authorizes Web-owned role projections and
exact prospective/historical context, so an implementation note—not a new
ADR—is the correct architecture action.

## Role Landing Pages

Every non-administrator persona receives a shared accessible dashboard with:

- a state-derived next action and link to assigned work;
- a plain-language description of the role's exact authority;
- explicit unavailable actions rather than omission alone;
- the server-authorized contract, agency, and NGO context;
- the prospective active configuration and exact profile references when the
  role may read them; and
- the exact historical invoice, review, or submitted-package context when
  assigned.

The NGO Approver renders a useful empty queue rather than disappearing when no
invoice is ready. Government review displays the submitted configuration and
profile ids/versions/hashes. The Auditor receives no active/draft configuration
access; it displays only submitted historical package evidence and contains no
form or button. React presentation is never an authorization input.

## Public Contract And Read-Model Changes

`configuration-contracts` and `event-contracts` advance additively to `2.1.0`.
`ActiveConfigurationDto` optionally exposes exact `documentProfiles`.
`AuditPackageDto` optionally exposes `configurationVersion` and
`documentProfiles`. Generated Pydantic and TypeScript consumers are rebuilt
from the registries.

Invoice draft and Government review responses add exact configuration and
profile references. Each reference is derived from the immutable configuration
version selected by the canonical invoice, not the current active pointer.
Provenance derives package profile references from the retained validation
input manifest. No client joins canonical data or invents an id/version/hash.

## Journey 12 Behavior

The canonical browser scenario was renamed to `journey12.spec.ts`, with
`scripts/run_journey12.sh` as the terminal runner. Compatibility Journey 11
commands invoke the same non-reduced Journey 12 path.

From fresh PostgreSQL and MinIO volumes the scenario proves:

1. Configuration Administrator login, exact v1 profile evidence, deterministic
   configuration test, assigned-human approval, and prospective activation.
2. NGO Preparer login and real worker processing for ledger/evidence, a
   supported English invoice, a supported Spanish invoice, a changed layout,
   and an unknown layout.
3. Exact English/Spanish profile context, human correction of draft OCR, and
   visible `needs_profile_review` with no canonical expense for unsupported
   layouts.
4. Deterministic validation and finding resolution.
5. Separate NGO Approver v1 attestation/package/submission.
6. Government Reviewer return of exact v1, NGO correction into v2, separate
   revalidation/re-attestation/repackaging/resubmission, and Government final
   approval of v2.
7. Configuration Administrator profile successor create/test/approve/stage,
   configuration v2 test/approve/supersede, and explicit future-only impact
   confirmation.
8. Preparer visibility of active profile/configuration v2 and Auditor
   reconstruction of both packages with original profile/configuration v1,
   unchanged v1 hash, and distinct v2 hash.

All persona changes use normal logout/login. Direct Administrator and Auditor
invoice-creation calls return `403`. No database edit, test endpoint, client
role switch, or manual state mutation is used.

## Determinism, Provenance, And Security

Pinned local OCR remains `tesseract-5.5.0-eng+spa`; draft fields require human
review. Deterministic contracts own profile matching, safe routing, validation,
lifecycle eligibility, and package reproduction. System/AI actors retain no
configuration activation, attestation, submission, return, or approval
authority.

Configuration/profile successor activation is prospective. Historical invoice
draft/read models, government context, validation inputs, package manifests,
and audit packages retain exact ids, versions, and hashes. Integration tests
assert equality across those projections. Existing tenant/role/zero-mutation
and append-only suites remain unchanged and passing.

Only the positive closed synthetic fixture catalog and reserved-domain
personas enter the run. No hosted provider, external model credential, brand,
customer data, or real personal data is introduced. Retained browser evidence
is local/CI synthetic development evidence and cannot certify production or
real-data use.

## Candidate Verification

| Command | Exit | Result |
| --- | ---: | --- |
| pinned `bash scripts/ci/run_static.sh` | 0 | Python 3.12.2/Node 20.20.2; format, Ruff, mypy, five generated registries/58 contracts, 197 persistence statements, 90 repository tests, 30 frontend tests, production build, and web boundary checks pass |
| `bash scripts/ci/run_hermetic.sh tmp/evidence/SUB-78/final-candidate-hermetic` | 0 | Two fresh PostgreSQL/MinIO passes run 217 tests each with equal reset fingerprint `98f77de03e5553b230c7956c0d8b8373b7ae12efd32c763a20deee8f3e7040fd` |
| `bash scripts/run_journey12.sh headless tmp/evidence/SUB-78/final-candidate-journey12-headless` | 0 | One expected, zero unexpected/flaky; clean Journey 12 passes in 20.3 seconds with 41 retained video, trace, screenshot, JSON, HTML, runtime-log, and Compose-state files |
| `bash scripts/run_journey12.sh headed tmp/evidence/SUB-78/final-candidate-journey12-headed` | 0 | The same scenario passes in default 650 ms paced headed mode in 1.4 minutes with 41 retained video, trace, screenshot, JSON, HTML, runtime-log, and Compose-state files |

Exact PR-head hosted CI, the machine-readable manifest, eight immutable-diff AI
reviews, merge, and clean post-merge reruns remain completion gates.

## Durable Evidence

- ADR: `docs/adr/0003-configurable-document-intake-mvp.md`
- Architecture/domain/data/boundary: `docs/architecture/`
- Journey: `docs/journeys/12-configurable-document-intake-mvp.md`
- Security/privacy: `docs/sdlc/poc-security-privacy.md`
- AI/configuration governance: `docs/sdlc/poc-ai-governance.md`
- Requirements traceability: `docs/sdlc/requirements-traceability.md`
- Prerequisites and evidence coverage: `docs/sdlc/issue-prerequisites.json` and
  `docs/sdlc/issue-evidence-coverage.json`
- Executable evidence: `services/api-workflow/tests/`,
  `apps/web-app/src/architecture.test.tsx`, and
  `tests/e2e/specs/journey12.spec.ts`
- Candidate artifacts: ignored `tmp/evidence/SUB-78/`
- PR manifest: ignored `tmp/evidence/SUB-78/pr/manifest.json` after immutable
  base/head and PR URL exist

## Review And Release Plan

The immutable PR diff requires Architecture/ADR, requirements traceability,
capability boundary, security/privacy, AI/configuration governance,
implementation/tests, Journey 12, and release-readiness AI review decisions.
Reviews inspect one immutable base/head diff and do not edit during the review
pass. Required fixes become new commits and trigger a full repeat.

No human code-review approval is required. Executable evidence, exact hosted
checks, immutable AI review, and post-merge verification are the code gate.
The final synthetic/local MVP decision may become `Certified` only after those
gates. Hosted production, real data, identity hardening, malware scanning,
backup/legal hold/retention, payment execution, and broader document support
remain outside this release and require separate human decisions.
