# ADR 0001: Core Architectural Pillars for Reimbursement Workflow Platform

## Status

Accepted

## Date

2026-07-09

## Context

The product domain is human-services reimbursement between nonprofit providers and government agencies. Nonprofits assemble reimbursement packages from ledgers, payroll reports, receipts, proof of payment, timesheets, and other supporting artifacts. Government agencies review those packages against contract budgets, agency rules, documentation requirements, and approval workflows.

The core product problem is not simply document extraction or invoice generation. The system must make reimbursement claims faster to prepare and review while preserving trust, oversight, and accountability across multiple organizations.

The platform therefore needs to support:

- Full traceability from source artifacts to extracted fields, invoice lines, validations, corrections, submissions, returns, approvals, and payment status.
- Agency- and contract-specific rules, forms, views, and workflows without custom code for every customer.
- Reliable and repeatable software behavior in a compliance-heavy environment.
- Human authority over attestations, waivers, exceptions, approvals, and final accountability.

## Decision

Adopt four core architectural pillars for the platform:

1. End-to-End Provenance
2. Configurable Reimbursement Ontology
3. Deterministic Execution, AI-Assisted Configuration
4. Human Authority Over Cross-Organizational Workflow

These pillars should shape the data model, workflow engine, validation system, document storage strategy, AI usage, permissions model, audit logging, and customer configuration surfaces.

## Pillar 1: End-to-End Provenance

Every claim, artifact, field, rule result, correction, decision, and handoff must be traceable.

The platform should behave as a provenance system for reimbursement claims. An invoice is not just a form; it is a graph of claims, evidence, validations, corrections, approvals, and stakeholder handoffs.

Core design implications:

- Store source documents and generated submission packages as immutable artifacts.
- Hash and version source artifacts, generated packages, and material derivations.
- Maintain lineage from each invoice amount back to source document, page/cell/bounding box, parser version, extraction confidence, and user correction history.
- Record validation runs with the exact invoice version, document versions, budget version, rule version, schema version, mapping version, and model/parser version used.
- Treat corrections as new lineage events rather than overwriting prior values.
- Maintain an append-only event log for material actions.
- Build queryable projections for product workflows, but keep enough event and lineage history to reconstruct how a submitted invoice was produced and reviewed.

Example traceability question the architecture must answer:

> For this claimed dollar amount, what source evidence supports it, who uploaded it, how was it extracted, what rule checked it, who corrected or waived it, what was submitted to the agency, and who approved or returned it?

## Pillar 2: Configurable Reimbursement Ontology

The system should expose a compact set of domain primitives that can be configured into agency-specific reimbursement workflows.

The goal is not to build a generic no-code platform. The goal is a domain-specific configuration system for reimbursement.

Core primitives:

- `Artifact`: source or generated object such as PDF, receipt, ledger export, payroll file, invoice package, or validation summary.
- `Schema`: expected structured shape of an artifact, form, or extracted output.
- `Field`: typed data element such as amount, date, vendor, employee, budget category, contract id, or payment reference.
- `Entity`: domain object such as invoice, expense, budget line, contract, provider, reviewer, or payment.
- `Relation`: link between artifacts and entities, such as supports, derives from, maps to, validates against, replaces, or amends.
- `Rule`: deterministic check over fields, entities, relations, budgets, dates, statuses, or documentation requirements.
- `Workflow`: states, transitions, approvals, returns, assignments, and amendment semantics.
- `View`: role-specific projection over the same underlying domain graph.
- `Template`: generated output format such as agency invoice form, review package, export file, or validation summary.
- `Event`: immutable record of a material action, decision, correction, or handoff.

Core design implications:

- Store contract setup, schemas, mappings, rules, workflows, templates, and views as versioned configuration.
- Support customer-specific configuration without hard-coding every agency workflow.
- Prefer composable domain primitives over a large set of one-off domain tables and custom pathways.
- Use a schema registry for structured outputs and customer-specific form shapes.
- Use mapping definitions to translate external artifacts into canonical fields and entities.
- Treat views as projections over shared canonical data, not separate stakeholder-specific copies.
- Version all configuration used in a submitted invoice.

## Pillar 3: Deterministic Execution, AI-Assisted Configuration

AI should do the minimum set of work required. Deterministic software should carry most of the operational weight.

The platform should use AI to help configure and validate the right deterministic behavior once, then rely on versioned software execution for repeatable runtime behavior.

Guiding principle:

> Use AI to help configure the machine; use deterministic software to run the machine.

Appropriate AI responsibilities:

- Infer likely schemas from customer documents.
- Suggest mappings from uploaded artifacts into the reimbursement ontology.
- Propose validation rules from contracts, policy documents, templates, and historical return comments.
- Classify documents and suggest extraction plans.
- Summarize issue threads or explain validation failures in user-facing language.
- Assist implementation specialists and customer admins during onboarding.

Responsibilities that should remain deterministic:

- Submission-blocking validation decisions.
- Budget availability checks.
- Required-document checks.
- Date eligibility checks.
- Workflow state transitions.
- Permission checks.
- Package generation from approved templates.
- Reproduction of historical validation results.

Core design implications:

- AI-generated configuration must be reviewed, tested, approved, and versioned before production use.
- Runtime validation should execute against explicit schemas, mappings, rules, workflows, and templates.
- The same inputs plus the same configuration versions should produce the same outputs.
- AI-derived extracted fields must carry source references, confidence, model version, and correction history.
- Compliance-critical rule results must be explainable without requiring trust in an opaque model response.
- The system should optimize toward reducing repeated AI calls in stable workflows.

Example target behavior:

> This invoice passed `Agency-DHS-ReimbursementRules-v14` using contract budget `C-21184-FY26-v3`, invoice schema `MonthlyVoucher-v5`, document mapping `QuickBooksLedger-v2`, and package template `AgencyReviewPacket-v6`.

## Pillar 4: Human Authority Over Cross-Organizational Workflow

The system should automate preparation, validation, routing, and evidence presentation, but humans retain authority over attestations, exceptions, waivers, returns, approvals, and final accountability.

The platform mediates between organizations with different incentives and legal responsibilities. The architecture must therefore enforce who is allowed to do what, when, against which version of the invoice, and with what downstream effect.

Core design implications:

- Model role-specific authority directly: nonprofit fiscal staff, nonprofit approvers, agency reviewers, agency supervisors, auditors, platform support, and system actors.
- Use explicit workflow state machines for invoice lifecycle, issue resolution, returns, amendments, approvals, and payment-status updates.
- Require the correct human actor for attestations, waivers, agency returns, approvals, escalations, and finalization.
- Ensure AI can recommend, classify, summarize, or draft, but cannot attest, waive, approve, or finalize.
- Lock submitted packages. Later changes must create amendments, returns, or resubmissions rather than silent mutation.
- Require rationale for human waivers, overrides, and exception handling.
- Make platform support actions constrained, visible, permissioned, and logged.
- Give auditors inspectability without mutation rights.
- Preserve a shared canonical invoice state across nonprofit and agency views.

Guiding principle:

> Humans keep judgment; the system keeps structure.

## Consequences

### Positive

- The system can earn trust from both nonprofits and agencies because submitted claims are reproducible and inspectable.
- Agency-specific workflows can be supported without fragmenting the codebase into customer-specific implementations.
- AI can accelerate onboarding and reduce manual setup while avoiding nondeterministic runtime decisions.
- Audit readiness becomes a product capability rather than an afterthought.
- Human reviewers and fiscal staff remain accountable for judgment calls, while software handles repetitive comparison and routing work.

### Negative

- Initial platform design is more complex than a simple document extraction or invoice-generation application.
- Versioning schemas, mappings, rules, workflows, templates, and artifacts increases implementation overhead.
- Building good configuration tooling requires upfront investment.
- Strict lineage and immutable artifact storage may increase data volume and operational cost.
- Human authority workflows require careful UX design so controls do not become cumbersome.

### Risks

- Over-configurability could turn the product into a generic workflow builder instead of a focused reimbursement platform.
- Under-configurability could force per-customer custom code and slow implementation.
- AI-assisted configuration could create unsafe rules if not reviewed and tested.
- Event and provenance models could become difficult to query unless paired with well-designed projections.

## Implementation Guidance

Start with a narrow pilot implementation that proves the pillars without overbuilding the full platform.

Minimum viable architecture:

- Immutable artifact storage for uploads and generated packages.
- Relational domain model for contracts, budgets, invoices, line items, issues, users, roles, and workflow state.
- Append-only event table for material actions.
- Versioned schemas, mappings, and deterministic rules.
- Validation engine that records every rule input and result.
- Explicit invoice state machine.
- Role-based permission checks for transitions and decisions.
- Basic configuration surface for contract budget, invoice template fields, and rule parameters.
- Manual review/approval for AI-suggested extraction or configuration.

Avoid early:

- A universal no-code workflow builder.
- Runtime AI as the source of truth for compliance decisions.
- Stakeholder-specific copies of the same invoice.
- Mutable submitted packages.
- Audit logging implemented only as application logs.

## Related Documents

- [Reimbursement Workflow Platform: Problem and Solution Statement](../../solution_requirements.md)
