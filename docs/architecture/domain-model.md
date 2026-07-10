# Domain Model

ContractView's domain model is a reimbursement provenance model. An invoice is not only a form or a list of line items; it is a graph of claims, evidence, configuration, validations, corrections, workflow decisions, generated packages, and stakeholder handoffs.

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
