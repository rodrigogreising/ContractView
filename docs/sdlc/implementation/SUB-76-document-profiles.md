# SUB-76 Deterministic Document Profiles And Intake Evidence

Status: In Review (immutable AI review fixes applied; recertification pending)

Linear project stage: Build

Branch: `codex/sub-76-deterministic-document-profiles`

Base SHA: `6d2437fa4d743ec470eac58692d0e4a0623b7736`

## Control And Scope

SUB-76 implements the runtime profile seam approved by ADR 0003. Its merged,
post-merge-verified prerequisites are SUB-17
`382876b7746e1147ee112e23bc80b95b90114d3a`, SUB-56
`d8f99ebd27a5d3d99a6d1ad59477e94acd142ce3`, SUB-63
`a15d93637c0f998de5dc07374f6a6c975586f876`, SUB-74
`70099d0f23f89adeddb82fe6ffd3adedd4d8c8cd`, and SUB-75
`6d2437fa4d743ec470eac58692d0e4a0623b7736`.

This leaf owns executable profile/intake contracts, capability-owned
persistence, deterministic English/Spanish fixtures and evaluation, pinned
local OCR, exact profile matching, noncanonical cluster suggestions, safe
changed/unknown routing, exact downstream version references, and profile
lifecycle commands. It does not implement the complete administrator
workspace (SUB-77) or terminal five-role Journey 12 certification (SUB-78).

## Executable Ontology And Ownership

The shared registries define versioned profile, fixture, evaluation,
fingerprint, cluster, match, route, ledger-match, source-location, and intake
result contracts. Generated Python and TypeScript consumers are produced from
the same registries. A profile composes existing artifact, typed-field,
configuration, event, and version-reference vocabulary; it is not a parallel
customer schema.

Configuration owns immutable profile versions, fixture sets, evaluations,
human approvals, lifecycle events, prospective active assignments, and draft
cluster associations. Extraction owns OCR executions, fingerprints,
noncanonical cluster projections, exact match results, and draft fields. Named
repository statements and machine ownership policy enforce that split. The
only runtime collaboration is an immutable Configuration query port that
returns exact active configuration/profile references.

## Deterministic Intake And Safe Routing

The pinned adapter records `tesseract-5.5.0-eng+spa`. The parser and fingerprint
specifications are respectively
`deterministic-document-profile-parser-v1` and
`document-layout-signals-v1`. The fingerprint is a canonical SHA-256 over the
declared media type, language, value-free normalized line-shape tokens,
whitespace-normalized non-empty-line geometry, and normalized anchor positions.
Blank-line variation from pinned OCR is ignored, while inserted, removed, or
reordered non-empty layout rows change the fingerprint and route to review.

Only an exact fingerprint in an active, content-hash-matched profile plus all
required normalized fields produces `recognized_profile_draft`. Changed,
unknown, incomplete, or unmatched input produces `needs_profile_review`, an
immutable artifact/OCR/fingerprint/match record, and a noncanonical cluster
projection. It creates no extraction field, canonical expense, validation run,
profile assignment, or activation. Administrator cluster confirmation creates
only a draft association.

Every recognized field records its exact source line and normalized label.
The runtime snapshot records artifact, raw OCR, provider/model, parser/schema,
fingerprint, profile, configuration, route, profile-governed ledger
reconciliation, raw OCR artifact hash, and result hash. Validation-input
manifests carry the exact profile, fingerprint, and configuration references
downstream.

## Governance And Authority

Profile transitions use `draft -> tested -> approved -> active -> superseded
-> retired`. Test evidence is computed from the immutable closed fixture set.
Testing rejects suites without at least two supported layouts plus explicit
changed and unknown cases; each metric uses only its intended case class, so
empty denominators cannot certify a profile. Configuration testing resolves
the exact profile id/version/hash, reproducible evaluation, and human approval
before it can record passing profile-reference evidence. Approval is an
explicit assigned Configuration Administrator action; activation validates
exact id, version, content hash, successful evidence, and approval.
Database constraints independently bind each authority record to the actor's
canonical user organization and contract/role assignment.

Profile, evaluation, approval, lifecycle, fingerprint, match, and cluster-
association evidence is append-only. Active assignments are prospective
pointers. Successor proof cannot rewrite the prior version or any retained
runtime reference. A governed configuration rollback may reactivate an exact
superseded/retired profile reference only after the rollback candidate is
retested and human-approved; it appends `profile_rollback_activated` rather
than rewriting prior active/superseded events.

## Fixture And Evaluation Contract

The deterministic catalog contains two supported English invoices, two
supported Spanish invoices, one changed layout, and one unknown document. Its
positive synthetic provenance is declared by the fixture catalog and generator;
acceptance does not rely on a forbidden-term blacklist. Expected fields and
source locations are exact, changed/unknown safe-routing is exact, and every
generated byte is covered by the fixture hash manifest.

## Immutable AI Review Remediation

The first immutable review of head
`9572a5bd3193bb7e819dddc259c0164589ff8cca` returned `Approved with required
fixes`. The remediation makes the approved contracts executable rather than
descriptive:

- shifted layouts with unchanged labels and values now fail exact matching;
- fixture kinds are closed shared vocabulary and underrepresented suites fail
  before any governed record is written;
- the profile-declared fingerprint specification and ledger field mapping are
  validated and executed;
- successors require the exact prior version, profile key, hash, and approved
  lifecycle evidence; and
- configuration test evidence cannot pass a nonexistent, hash-mismatched,
  unevaluated, or unapproved profile reference.

Focused remediation evidence passes 38 database/OCR/workflow tests and 14 pure
domain/fixture tests. Full and hermetic counts are updated after the new
immutable head is committed.

## Durable Evidence

- ADR: `docs/adr/0003-configurable-document-intake-mvp.md`
- Architecture: `docs/architecture/system-map.md`, `data-flow.md`,
  `domain-model.md`, `service-boundaries.md`, `poc-boundary-review.md`, and the
  machine ownership/dependency policies
- Security/privacy: `docs/sdlc/poc-security-privacy.md`
- AI/configuration governance: `docs/sdlc/poc-ai-governance.md`
- Requirements: `docs/sdlc/requirements-traceability.md`
- Journey checkpoint: `docs/journeys/12-configurable-document-intake-mvp.md`
- Executable tests: `test_document_intake_domain.py`,
  `test_document_profiles.py`, `test_extraction.py`,
  `test_extraction_review.py`, `test_validation.py`, `test_fixtures.py`, and
  `test_shared_contracts.py`
- PR evidence manifest: `tmp/evidence/SUB-76/pr/manifest.json` after an
  immutable head exists

## Acceptance Evidence

Pre-review evidence proves five shared registries and 58 generated contracts,
197 named persistence statements, 57 table owners, clean numbered migration
and reset, real English and Spanish local OCR, exact supported-field/source
results, deterministic replay, safe negative routing with zero canonical
mutation, cluster-confirmation authority, immutable route evidence, and exact
downstream manifest references. Final static, full API, two-pass hermetic,
hosted, and immutable AI-review results are recorded in the PR manifest and
Linear before completion.

## Test Results

Recorded on 2026-07-13 for the remediation candidate:

| Command | Exit | Result |
| --- | ---: | --- |
| `python3 scripts/check_shared_contracts.py` | 0 | Five registries and 58 generated contracts pass drift, schema, and consumer checks |
| `python3 scripts/check_persistence_statements.py` | 0 | 197 owner/consumer-scoped named statements and generated ids pass |
| `python3 scripts/check_module_boundaries.py` | 0 | 57 table owners and 197 statements pass import, owner, and collaboration policy |
| pinned `bash scripts/ci/run_static.sh` | 0 | Python 3.12.2/Node 20.20.2; format, Ruff, mypy, contracts, persistence, architecture/SDLC policies, 90 script tests, 24 frontend tests, production build, and web boundaries pass |
| focused pure domain/fixture suite | 0 | 14 tests pass fixed-spec execution, conservative layout fingerprints, non-vacuous fixture governance, deterministic evaluation, and generated-fixture integrity |
| focused clean profile/OCR/workflow suite | 0 | 38 tests pass profile evidence, exact predecessor governance, configuration-reference validation, configured ledger mappings, real OCR, and safe changed/unknown routing |
| clean Docker API/workflow suite | 0 | 217 tests pass, including real English/Spanish OCR, deterministic replay, safe negative routing, immutability, authorization, provenance, and downstream manifests |

## Review Plan

- Requirements traceability
- ADR/architecture
- Capability boundary
- Security/privacy
- AI/configuration governance
- Implementation/tests

No default human code-review approval is required. Approval depends on
executable evidence, hosted checks, and six immutable AI review decisions,
followed by clean post-merge verification.
