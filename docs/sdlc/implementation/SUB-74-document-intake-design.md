# SUB-74 Configurable Document-Intake MVP Design Evidence

Status: In Progress

Linear project stage: Design Review

Branch: `codex/sub-74-document-intake-design`

Base SHA: `0d41b540c47f116f6b25d88aea39138a4ca2f043`

## Control And Scope

SUB-74 is the first dependency-ready leaf in the frozen SUB-73 MVP scope. Its
prerequisites are merged and post-merge verified: SUB-17 through the terminal
Journey 11 certification merge `382876b7746e1147ee112e23bc80b95b90114d3a`,
SUB-56 at `d8f99ebd27a5d3d99a6d1ad59477e94acd142ce3`, and SUB-80 at
`0d41b540c47f116f6b25d88aea39138a4ca2f043`.

This PR defines product scope, ADR, capability ownership, data flow, domain
types, security/privacy, AI/configuration governance, requirements trace,
Journey 12, and a positive machine-readable design contract. It introduces no
runtime route, table, migration, fixture bytes, UI behavior, or deployment.

## Decisions Produced

- The MVP remains an enforceable modular monolith.
- `DocumentProfileVersion` composes the existing ontology and is owned by
  Configuration.
- `DocumentClusterProjection` is deterministic, Extraction-owned, and
  noncanonical.
- Changed/unknown layouts create `needs_profile_review` and no canonical
  expense.
- Profiles use the complete governed lifecycle and activate only through an
  exact, prospective configuration-bundle reference.
- The fixture scope is narrow, closed, synthetic, deterministic, English and
  Spanish vendor invoices.
- Pinned local OCR is permitted; hosted models, runtime LLMs, AI-assisted
  profile drafting, automatic assignment, and system/AI authority are not.
- One canonical workflow supplies five role projections; UI visibility does
  not authorize commands.

## Durable Evidence

- Product: `docs/product/document-intake-mvp-charter.md`
- ADR: `docs/adr/0003-configurable-document-intake-mvp.md`
- Machine contract: `docs/architecture/document-intake-mvp-policy.json`
- Architecture/boundaries: `docs/architecture/system-map.md`,
  `data-flow.md`, `domain-model.md`, `service-boundaries.md`, and
  `poc-boundary-review.md`
- Journey: `docs/journeys/12-configurable-document-intake-mvp.md`
- Security/privacy and AI/configuration governance: `docs/sdlc/poc-security-privacy.md`
  and `docs/sdlc/poc-ai-governance.md`
- Traceability: `docs/sdlc/requirements-traceability.md`

## Executable Evidence Plan

`scripts/tests/test_mvp_design_evidence.py` validates the positive machine
contract, exact lifecycle/ownership, ontology composition, deterministic
cluster and safe-routing invariants, synthetic fixture evaluation, automation
prohibitions, five-role authority, narrative links, requirement trace, and
evidence/prerequisite registries. The repository static gate supplies format,
lint, contract, boundary, registry, and existing regression checks.

## Implementation And Test Results

Recorded at `2026-07-13T13:22:31Z`:

| Command | Exit | Result |
| --- | ---: | --- |
| `python3 -m pytest -q scripts/tests/test_mvp_design_evidence.py` | 0 | 6 positive design-contract tests passed |
| `python3 scripts/check_formatting.py` | 0 | 376 structured/text files passed |
| `python3 -m ruff check scripts/tests/test_mvp_design_evidence.py` | 0 | No findings |
| `python3 -m mypy scripts/tests/test_mvp_design_evidence.py` | 0 | No findings |
| `bash scripts/ci/run_static.sh` with repository-pinned Python/Node paths | 0 | Toolchains, format, Ruff, mypy, shared contracts, 177 persistence statements, 47 table owners, architecture/delivery/recovery policies, 90 Python tests, 24 frontend tests, production build, and web boundaries passed |

The focused tests inspect structured positive contracts and exact expected
catalogs, lifecycle, outcomes, metrics, authority, and references. They do not
claim privacy or neutrality from a blacklist scan.

The immutable PR review result remains pending until the branch is committed,
pushed, and the draft PR plus schema-valid manifest identify exact base/head
SHAs. Review passes must not edit the PR; required fixes, if any, become later
commits and trigger a new review.

## Review Plan

- Product intake
- Requirements traceability
- ADR/architecture
- Boundary review
- Security/privacy
- AI/configuration governance
- Journey certification design
- Implementation/tests

No human code-review gate is required. Approval requires executable evidence,
hosted checks, and immutable AI review decisions before merge, followed by
clean post-merge verification.

## AI Review Pass 1

The immutable diff from base `0d41b540c47f116f6b25d88aea39138a4ca2f043`
to head `fa094103d42ba60407b67684c4c55ace66fedceb` received `Approved with
required fixes`. Product intake was approved; the other applicable reviews
required:

- explicit boundary and release-evidence columns in the MVP trace;
- positive machine properties/tests for submitted immutability, single
  canonical stakeholder state, approved-only activation, zero unknown-layout
  validation, source-location exactness, and runtime version references; and
- removal of the stale pre-certification REC-12 statement from the POC boundary
  evidence.

The fixes are additional commits on PR #22. Checks and the evidence manifest
must be regenerated for the new head before review pass 2.

Fix verification recorded at `2026-07-13T13:30:14Z`:

- focused positive design evidence: 6 passed;
- formatting, Ruff, and mypy: passed;
- complete static gate: 90 Python tests, 24 frontend tests, production build,
  and every contract/persistence/boundary/policy check passed; and
- updated policy/test SHA-256 values are retained in the regenerated PR
  manifest.
