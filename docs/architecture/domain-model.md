# Domain Model

ContractView's domain model is a reimbursement provenance model. An invoice is not only a form or a list of line items; it is a graph of claims, evidence, configuration, validations, corrections, workflow decisions, generated packages, and stakeholder handoffs.

The vocabulary is governed by the [modular-monolith policy](modular-monolith-policy.json).
SUB-61 implements it as executable, versioned shared contracts rather than
free-form runtime dictionaries. Canonical inputs are the four
`packages/*-contracts/contract.json` registries plus
`packages/domain-types/contract.json`; generated consumers are
`services/api-workflow/app/domain/shared_contracts.py` and
`apps/web-app/src/generated/contracts.ts`.

## Core Primitives

| Primitive | Definition | Ownership notes |
| --- | --- | --- |
| `Artifact` | Source or generated object such as PDF, receipt, ledger export, payroll file, invoice package, validation summary, or manifest. | Immutable once registered; material derivations are new artifact versions. |
| `Schema` | Expected structured shape of an artifact, form, import, extraction output, or template input. | Versioned configuration. |
| `Field` | Typed data element such as amount, date, vendor, employee, budget category, contract id, payment reference, or attestation field. | Must carry source and correction lineage when material. |
| `Entity` | Domain object such as invoice, expense, budget line, contract, provider, reviewer, issue, payment status, or user role. | Canonical entities are not duplicated per stakeholder. |
| `Relation` | Link between artifacts and entities, such as supports, derives from, maps to, validates against, replaces, amends, submits, returns, or approves. | Enables reconstruction and evidence traversal. |
| `Rule` | Deterministic check over fields, entities, relations, budgets, dates, statuses, documentation requirements, or workflow completeness. | Versioned configuration with test evidence. |
| `Workflow` | States, transitions, approvals, returns, assignments, issue resolution, amendments, and payment-status semantics. | Explicit and permissioned. |
| `View` | Role-specific projection over canonical data for nonprofit, agency, auditor, support, or admin users. | Must not create stakeholder-specific copies. |
| `Template` | Generated output format such as agency invoice form, review package, export file, package manifest, or validation summary. | Versioned configuration. |
| `Event` | Immutable record of a material action, decision, correction, handoff, configuration activation, or system result. | Append-only; corrections are represented as later events. |
| `ValidationRun` | Deterministic evaluation record for an invoice version using exact artifact, budget, rule, schema, mapping, workflow, template, and parser/model versions. | Required for certification and reproducibility. |
| `ConfigurationBundle` | Versioned set of schemas, mappings, rules, workflows, views, templates, and rule parameters active for a contract or pilot context. | Must follow lifecycle before production activation. |
| `InvoiceSnapshot` | Immutable invoice content and material-revision identity used by validation, attestation, package, submission, return, and approval evidence. | Distinct from an editable draft aggregate. |
| `PackageManifest` | Deterministic package inputs, paths, hashes, template/configuration versions, and reproduction metadata. | Immutable; owned by package generation. |
| `ContractContextDto` | Server-authorized contract identity and agency/NGO ownership names exposed to a signed-in workspace. | Generated shared DTO; derived from canonical ownership/assignments, never client authority. |

### Typed Relation Direction

Relation direction is semantic and therefore part of the executable ontology:

| Relation | Source -> target |
| --- | --- |
| `supports` | Source artifact/entity -> supported invoice |
| `derived_from` | Derived package/artifact -> immutable source snapshot/artifact |
| `maps_to` | Imported expense/entity -> canonical invoice |
| `validated_by` | Invoice snapshot -> validation run |
| `submitted_as` | Submission-stage invoice snapshot -> submission |
| `returned_as` | Returned predecessor invoice -> editable successor invoice |
| `amends` | Corrected successor invoice -> predecessor invoice |
| `approved_as` | Reviewed submission -> government decision |

Tests must verify source and target kinds/versions, not only the presence of a
relation-type string.

## Executable Contract Rules

- Core primitives, lifecycle states, actor roles, resource kinds, relation
  kinds, event names, reason codes, and version references are closed typed
  vocabulary.
- Unknown vocabulary is rejected at the owning application boundary.
- API, worker, persistence, and web DTOs must use compatible shared contract
  versions.
- Domain contracts contain no FastAPI, SQL, MinIO, queue, or provider SDK
  types.
- Contract packages use semantic versions. Minor changes are additive and
  optional; closed-vocabulary, required-field, removal, or semantic changes
  require a major version and coordinated consumer migration.

## Configuration Versus Runtime

SUB-61 currently executes configuration contracts for `Rule`, `Workflow`,
`View`, `Template`, and `ConfigurationBundle`, with exact schema/mapping
version references. It executes runtime contracts for `Artifact`, typed
`Field`, `Entity`, `Relation`, the versioned `Event` envelope, and
`ValidationRun`. REC-06 adds executable schema/mapping definitions; REC-08 and
REC-09 add `InvoiceSnapshot`, typed event/relation payloads, and
`PackageManifest`. Those later contracts remain target-model requirements
rather than SUB-61 completion claims.

Configuration activation is prospective. Active versions are immutable.
Runtime records always carry exact configuration, artifact, invoice, contract,
budget, schema, mapping, rule, workflow, view, template, and parser/model
references as applicable. Re-validation and re-generation create new runtime
records; they never overwrite historical evidence.

## Configuration Lifecycle

All production configuration must move through:

1. Draft.
2. Tested.
3. Approved.
4. Active.
5. Superseded.
6. Retired.

Activation requires an authorized actor, timestamp, rationale, test evidence, affected contracts, and rollback or supersession path.

AI-generated configuration may enter draft state, but it cannot become active until reviewed, tested, approved, and versioned.

## Invoice Lifecycle

The canonical invoice lifecycle should support:

1. Draft.
2. Uploading.
3. Extracting.
4. Needs provider review.
5. Validating.
6. Issues open.
7. Ready for nonprofit approval.
8. Approved by nonprofit.
9. Submitted to agency.
10. In agency review.
11. Returned.
12. Agency approved.
13. Paid.
14. Archived.
15. Voided/amended.

Each transition must be permissioned, logged, and linked to a specific invoice version.

## Lineage Requirements

For every material claimed amount, the system must be able to answer:

- Which source artifact supports it?
- Which page, cell, row, bounding box, or source location contains the evidence?
- Which parser, importer, model, prompt, mapping, and schema produced the draft field?
- What confidence was assigned when extraction was probabilistic?
- Who corrected, excluded, waived, or accepted risk?
- Which validation rule checked it?
- Which invoice and package version submitted it?
- Who approved, returned, or finalized it?

## Deterministic Runtime Boundary

The following must be deterministic at runtime:

- Submission-blocking validation.
- Budget availability checks.
- Required-document checks.
- Date eligibility checks.
- Workflow state transitions.
- Permission checks.
- Package generation from approved templates.
- Historical validation reproduction.

AI may suggest, summarize, classify, draft, and assist configuration. AI must not attest, waive, approve, finalize, or become the unreviewed source of compliance truth.

## Release-Certification Data

Certified releases must preserve evidence for:

- Artifact hashes and versions.
- Configuration bundle versions.
- Validation runs and rule inputs.
- Workflow transition events.
- Human authority events.
- Generated package hashes and manifests.
- Audit reconstruction queries or exports.

## Document-Intake MVP Types

`DocumentProfileVersion` is a Configuration-owned composition of the existing
`Artifact`, `Schema`, typed `Field`, `Mapping`, `Rule`, `Workflow`, `View`,
`ConfigurationBundle`, and `Event` primitives. It is not a second ontology.
An immutable version contains the artifact class, BCP 47 language tag,
required/source-located fields, normalization and ledger-match rules,
fingerprint specification, fixture-set version, evaluation-evidence hash, and
predecessor/successor references.

`DocumentClusterProjection` is an Extraction-owned, noncanonical read model. A
versioned deterministic fingerprint is computed from declared artifact media,
language, normalized OCR tokens, page geometry, and anchor positions. The
projection can support an administrator suggestion but cannot create a profile
assignment or any lifecycle event.

Runtime matching records either `recognized_profile_draft` with the exact
active profile/configuration references or `needs_profile_review` with retained
artifact/OCR/fingerprint evidence. The latter creates no canonical expense.
Existing invoice snapshots and downstream evidence retain their original exact
references after a successor profile activates.

The shared-contract registry changes needed to make these concepts executable
belong to SUB-75 and SUB-76. SUB-74 defines and tests the design contract only.
