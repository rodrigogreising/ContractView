# ADR 0003: Configurable Document-Intake MVP

## Status

Accepted for implementation after the SUB-74 design PR is approved, merged,
and post-merge verified

## Date

2026-07-13

## Context

The certified role-based POC proves one synthetic extraction-to-approval path,
but its bounded configuration form and single fixture parser do not establish a
governed document-intake product. The MVP must support reusable English and
Spanish vendor-invoice layouts, make configuration understandable to an
administrator, route unknown layouts safely, and preserve exact historical
behavior after configuration changes.

The decision must extend ADR 0001's configurable ontology and ADR 0002's
enforceable modular monolith. It must not introduce a new deployable, hidden
cross-capability persistence, client authority, runtime LLM dependency, or a
second canonical invoice model.

## Decision

### 1. A document profile is versioned configuration

`DocumentProfileVersion` is a Configuration-owned aggregate composed from the
existing ontology: `Artifact`, `Schema`, typed `Field`, `Mapping`, `Rule`,
`Workflow`, `View`, `ConfigurationBundle`, and `Event`. It is not a new generic
workflow system or customer-specific code path.

Each immutable profile version records the artifact class, BCP 47 language
tag, synthetic vendor aliases, required fields, source-location contract,
normalization rules, ledger-match rules, fingerprint specification, fixture
set, evaluation evidence, and predecessor/successor references.

Profiles use the complete governed lifecycle:

`draft -> tested -> approved -> active -> superseded -> retired`

Testing freezes a candidate and produces immutable evidence. A canonically
assigned human Configuration Administrator approves it. A profile becomes
effective only when a prospectively activated `ConfigurationBundle` references
its exact id and version. Rollback creates a new tested successor.

### 2. Clusters are deterministic projections, never configuration authority

Extraction owns `DocumentClusterProjection`, a disposable read model computed
from canonicalized artifact media type, language tag, normalized local-OCR
tokens, page geometry, and anchor positions. The fingerprint is
`sha256-canonical-json-v1` over explicit versioned inputs.

The projection may suggest that artifacts form a document family. It cannot
assign, create, approve, or activate a profile. Administrator confirmation
invokes a Configuration command that creates a draft association and still
requires fixture testing, human approval, and bundle activation.

### 3. Unknown layouts fail safe before canonical invoice use

An exact active profile match produces `recognized_profile_draft`. All fields
remain draft until human review. No match or a changed layout produces
`needs_profile_review`, retains artifact/OCR/fingerprint evidence, and creates
no canonical expense or validation result.

Unsupported routing is an explicit deterministic result, not an exception that
silently falls back to a generic extractor.

### 4. Runtime evidence references exact versions

Extraction results retain artifact hash, source locations, OCR/parser versions,
fingerprint specification, profile id/version, configuration bundle version,
and human review. Invoice snapshots, validation inputs, packages, submissions,
and audit reconstruction retain the same exact profile/configuration references.

Activation is prospective. Existing invoices and submitted packages are never
reinterpreted against a newer profile. Reprocessing creates a new explicit
runtime record and cannot rewrite historical evidence.

### 5. Capability ownership remains inside the modular monolith

| Concern | Canonical owner | Collaboration |
| --- | --- | --- |
| Profile definitions, lifecycle, fixtures, evaluation evidence, associations, and active bundle references | Configuration | Configuration commands and immutable version queries |
| Artifact bytes and hashes | Artifacts | Immutable artifact query port |
| OCR executions, fingerprints, cluster projections, profile matches, and draft fields | Extraction | Versioned job plus immutable extraction snapshot |
| Invoice versions and snapshots | Invoices | Exact profile/configuration references in immutable snapshots |
| Validation/package/workflow behavior | Existing Validation, Packages, and Workflow owners | Existing command/query ports and retained manifests |
| Profile lifecycle events, source lineage, and reconstruction | Provenance | Append-only evidence writer and read-only audit model |
| Administrator and role landing pages | Web projections | Generated HTTP DTOs only; no canonical data or authority |

No new network service, table-sharing exception, repository escape hatch, or
cross-capability command SQL is authorized. SUB-75 and SUB-76 must extend the
shared executable contracts and physical table/statement ownership before
runtime data is added.

### 6. The MVP has no runtime AI dependency

Pinned local OCR is allowed as a replaceable adapter and its version is an
input. Hosted models, runtime LLM calls, AI-assisted profile drafting, opaque
profile classification, and AI/system activation are prohibited. Matching,
normalization, ledger reconciliation, validation, workflow, and package
generation are deterministic.

### 7. Views explain one canonical workflow

The Configuration Administrator receives the full configuration/profile
governance workspace. NGO Preparer, NGO Approver, Government Reviewer, and
Auditor receive lightweight role landing pages with next action, authority
explanation, and exact profile/configuration context. They remain projections
over shared canonical state and never grant authority.

## Consequences

### Positive

- Document support expands through explicit ontology contracts instead of
  customer-specific parsing branches.
- Unknown layouts cannot silently contaminate canonical invoice state.
- Configuration and profile changes remain testable, explainable, prospective,
  and historically reproducible.
- Local deterministic behavior avoids hosted model cost, data transfer, and
  opaque runtime authority.
- Capability seams remain suitable for later extraction without distributed
  deployment complexity.

### Negative

- Administrators must maintain fixtures and approve profile changes.
- Only two narrow vendor-invoice profiles are supported initially.
- Deterministic layout fingerprints are intentionally conservative and will
  route harmless layout changes to review.
- English/Spanish source handling does not provide a localized UI.

### Risks And Controls

| Risk | Control |
| --- | --- |
| Profile overfitting | Versioned multi-fixture evaluation plus changed/unknown negative cases |
| Configuration drift | Exact bundle/profile references and content hashes on all runtime evidence |
| Cluster suggestion treated as fact | Projection is noncanonical; explicit administrator confirmation and lifecycle required |
| OCR/version drift | Pin and record OCR/parser version; different input identity creates new evidence |
| Cross-tenant profile leakage | Contract/agency assignment and canonical scope resolve every profile command/query |
| Historical reinterpretation | Prospective activation and immutable invoice/validation/package references |

## Alternatives Rejected

- **Runtime LLM classification/extraction:** nondeterministic, unnecessary for
  the narrow fixture scope, and inconsistent with the MVP's no-hosted-model
  decision.
- **Automatic cluster-to-profile assignment:** converts a similarity projection
  into configuration authority and can misclassify unknown layouts.
- **Mutable profiles edited in place:** destroys reproducibility and audit
  reconstruction.
- **Profile logic in React or per-customer branches:** bypasses canonical
  ownership and fragments the ontology.
- **A new profile microservice:** adds network and transaction complexity
  without an established scaling or ownership need.

## Implementation Gates

- SUB-75: lifecycle read models, exact version references, authorization, and
  provenance.
- SUB-76: executable shared contracts, persistence ownership, deterministic
  fingerprint/match/extraction, fixtures, and safe routing.
- SUB-77: Configuration Administrator projection and commands through generated
  DTOs.
- SUB-78: role landing pages and Journey 12 terminal certification.

## SUB-75 Implementation Note: Explainable Configuration Evidence

SUB-75 implements the Configuration-owned lifecycle seam needed before profile
execution. Editable drafts now carry an optimistic revision. Save and test
commands compare that revision inside the owner transaction; stale commands
fail before any version or evidence record is appended. Governed versions,
test evidence, approvals, and lifecycle events remain immutable.

Activation and supersession rederive the candidate payload hash, deterministic
test report, result hash, suite version, and approval binding from the exact
immutable version. A lifecycle label alone is therefore insufficient to
activate a candidate. The active pointer remains prospective.

Version detail is canonical Configuration data. Human-readable diff,
activation impact, and configuration-to-runtime references are explicitly
noncanonical, content-hashed projections. A declared read model may join exact
invoice, validation, package, submission, snapshot, and audit-event references
for display and reconstruction, but it exposes no command or write port.
Capability owners retain their original tables and mutation authority.

The public HTTP paths evolve additively through generated shared DTOs. Full
history/detail/projection access and every mutation require the canonically
assigned Configuration Administrator. Other roles continue to receive only
their existing scoped, read-only active-configuration or audit projections.
The bounded evidence panel delivered here proves the DTO seam; SUB-77 remains
responsible for the complete administrator workspace.

## SUB-76 Implementation Note: Executable Profiles And Safe Intake

SUB-76 makes the profile composition executable through shared configuration,
domain, event, rule, and extraction contracts with generated Python and
TypeScript consumers. Configuration owns immutable profile definitions,
fixtures, evaluations, approvals, lifecycle events, active pointers, and draft
cluster associations. Extraction owns OCR, fingerprints, noncanonical cluster
projections, exact match records, and draft fields. The ownership catalog and
named statements enforce this without a new deployable.

The runtime uses pinned local English/Spanish Tesseract plus versioned,
deterministic parsing and fingerprint specifications. Only an exact active
profile fingerprint with complete required fields produces a draft. Changed,
unknown, or incomplete input retains immutable artifact/OCR/fingerprint/match
evidence and routes to `needs_profile_review` with no canonical expense,
validation, assignment, or activation mutation.

Profile activation binds exact id/version/hash, successful immutable fixture
evidence, and assigned-human approval to the active configuration transaction.
Authority evidence independently proves canonical user organization and
contract-role assignment. Runtime match records and validation manifests carry
the exact configuration, profile, OCR/parser, and fingerprint identities, so a
future profile successor cannot reinterpret prior evidence.

A configuration rollback that restores an exact historical profile reference
is a new prospective activation, not history mutation. It must pass the normal
tested/approved configuration rollback gate and append an explicit profile
rollback-activation event; prior active, superseded, and retired events remain
unchanged.

## Related Evidence

- `docs/product/document-intake-mvp-charter.md`
- `docs/architecture/document-intake-mvp-policy.json`
- `docs/architecture/service-boundaries.md`
- `docs/journeys/12-configurable-document-intake-mvp.md`
- `docs/sdlc/requirements-traceability.md`
