# Reimbursement Workflow Platform: Problem and Solution Statement

Prepared: 2026-07-09

## Goal

This document captures the problem and solution for software that assembles, validates, routes, and audits reimbursement invoices between human-services nonprofits and government agencies.

The aim is to describe a neutral, regulation-agnostic product concept: a platform that reduces reimbursement friction while preserving compliance, review authority, and auditability.

## Business Understanding

Human-services reimbursement is a high-friction workflow between nonprofit providers and government agencies. A useful product in this space assembles and validates contract invoices for government approval and payment, reducing administrative cycle time without weakening oversight.

The business problem is not generic invoice automation. It is a regulated reimbursement workflow where:

- Nonprofits incur expenses while delivering public services.
- Contracts define reimbursable budget categories, caps, documentation requirements, and agency-specific review rules.
- Nonprofits submit invoice packages with ledgers, receipts, proof of payment, timesheets, payroll records, and other backup.
- Agency reviewers manually compare invoice lines against contract budgets and rules.
- Errors are often found late, creating serial revision cycles, delayed payment, nonprofit cash-flow stress, and agency backlog.
- Oversight still matters. The system must accelerate review without removing agency approval authority.

The core solution opportunity is upstream validation: catch compliance, documentation, budget, and formatting problems before a claim enters the agency review queue.

## Product Thesis

The product should convert messy reimbursement evidence into an agency-ready invoice package with a traceable validation record.

The most important design principle: automate comparison and assembly, but preserve human judgment, accountability, and auditability.

## Stakeholders

### Government Agency Finance Reviewer

Primary job: approve or return reimbursement claims while protecting public funds.

Needs:

- A clean review queue with pre-screened invoices.
- Confidence that invoice lines match contract budgets and agency rules.
- Fast access to evidence behind every amount.
- Clear reason codes for flags.
- Audit-ready action history.
- Ability to approve, return, escalate, or request clarification.

### Government Program Officer

Primary job: ensure contracted services are delivered and funded appropriately.

Needs:

- Visibility into provider status and bottlenecks.
- Ability to distinguish administrative defects from substantive program concerns.
- Aggregate reporting on recurring provider issues.
- Configurable rules that reflect program-specific policies.

### Nonprofit Fiscal Staff

Primary job: get reimbursed accurately and quickly while maintaining compliance.

Needs:

- Upload data in native formats.
- Avoid manual re-entry into agency templates.
- See all validation problems before submission.
- Understand exactly what needs to be fixed.
- Collaborate with program/payroll/bookkeeping staff.
- Track invoice status after submission.

### Nonprofit Executive/Operations Leadership

Primary job: protect cash flow and operational continuity.

Needs:

- Predictable payment timeline.
- Portfolio-level view of outstanding invoices and amounts.
- Exportable history for board reporting, audits, and process improvement.

### Auditor/Comptroller/Read-Only Oversight Role

Primary job: verify that public funds were reviewed, approved, and paid according to rules.

Needs:

- Immutable audit trail.
- Chain of custody for uploaded documents and generated invoice packages.
- Searchable history by agency, nonprofit, contract, invoice, user, rule, date, and amount.

### Platform Operations / Customer Support

Primary job: onboard contracts, configure rules, support users, and monitor quality.

Needs:

- Admin tooling for tenant setup, contract import, template configuration, and rule maintenance.
- Safe access controls for customer support.
- Quality dashboards for extraction accuracy, rule false positives, and review-cycle metrics.

## Core User Outcomes

1. A nonprofit can close its books, upload backup, resolve validation issues, approve the final invoice, and submit to the agency without manually compiling the full package.
2. An agency receives invoices that have already been checked against contract budgets, documentation requirements, and agency rules.
3. Every material decision is traceable: source document, extracted field, configuration version, rule result, user action, timestamp, and final submitted artifact.
4. Reviewers spend time on exceptions and judgment calls instead of repetitive line-by-line matching.
5. Leadership can see where delays, recurring errors, and compliance risks originate.

## Architectural Requirements

The requirements in this document are governed by [ADR 0001: Core Architectural Pillars for Reimbursement Workflow Platform](docs/adr/0001-core-architectural-pillars.md). Product scope should be evaluated against four architectural requirements.

### End-to-End Provenance

The system must treat each reimbursement invoice as a graph of claims, source artifacts, extracted fields, corrections, validations, generated packages, submissions, returns, approvals, and payment-status updates.

Requirements:

- Source uploads and generated submission packages must be stored as immutable, versioned artifacts with hashes or immutable object references.
- Each invoice line and material field must retain lineage to source artifact, source location, parser/model version, extraction confidence where applicable, mapping version, and correction history.
- Corrections, exclusions, waivers, resubmissions, returns, approvals, and payment-status changes must be recorded as append-only events rather than silent overwrites.
- Validation runs must record the exact invoice version, artifact versions, contract/budget version, schema version, mapping version, rule version, workflow version, template version, and model/parser version used.
- Queryable projections may support fast product workflows, but the event and lineage records must be sufficient to reconstruct what was submitted, how it was produced, and who acted on it.

Acceptance criteria:

- A reviewer can answer, for any claimed amount, what evidence supports it, how it was extracted or imported, what rules checked it, who changed or waived it, and what package version was submitted.
- A historical invoice remains reproducible even after contract terms, templates, mappings, rules, or parser versions change.

### Configurable Reimbursement Ontology

The product must support agency-specific reimbursement workflows through versioned domain configuration, not customer-specific code paths.

Core configurable primitives:

- `Artifact`: source or generated object such as PDF, receipt, ledger export, payroll file, invoice package, or validation summary.
- `Schema`: expected structured shape of an artifact, form, or extracted output.
- `Field`: typed data element such as amount, date, vendor, employee, budget category, contract id, or payment reference.
- `Entity`: domain object such as invoice, expense, budget line, contract, provider, reviewer, or payment.
- `Relation`: link between artifacts and entities, such as supports, derives from, maps to, validates against, replaces, or amends.
- `Rule`: deterministic check over fields, entities, relations, budgets, dates, statuses, or documentation requirements.
- `Workflow`: states, transitions, approvals, returns, assignments, and amendment semantics.
- `View`: role-specific projection over the same underlying canonical data.
- `Template`: generated output format such as agency invoice form, review package, export file, or validation summary.
- `Event`: immutable record of a material action, decision, correction, or handoff.

Requirements:

- Contract setup, schemas, mappings, rules, workflows, templates, and views must be versioned configuration.
- Configuration must have a lifecycle: draft, tested, approved, active, superseded, and retired.
- Production activation of configuration must require authorized approval and test evidence.
- Submitted invoices must reference the exact configuration bundle used to assemble, validate, and generate the package.
- Role-specific views must be projections over shared canonical invoice state, not separate nonprofit and agency copies.

### Deterministic Execution, AI-Assisted Configuration

The system may use AI to reduce setup and document-processing labor, but compliance-critical runtime decisions must remain deterministic, versioned, explainable, and reproducible.

Requirements:

- Submission-blocking validation decisions, budget checks, required-document checks, date eligibility checks, workflow transitions, permission checks, and package generation must be deterministic.
- The same inputs plus the same configuration versions must produce the same validation results and generated package.
- AI-generated schemas, mappings, rules, summaries, classifications, or extraction plans must be reviewed, tested, approved, and versioned before production use.
- AI-derived fields must carry source references, confidence, model/prompt/parser version, and correction history.
- Advisory risk signals may prioritize review, but must not approve, waive, attest, finalize, or block submission unless implemented as explicit deterministic rules.

### Human Authority Over Workflow

The system must automate preparation, validation, routing, and evidence presentation while preserving human authority over attestations, waivers, exceptions, returns, approvals, and final accountability.

Requirements:

- Workflow state transitions must be explicit, permissioned, and logged against a specific invoice version.
- Attestations, waivers, accepted risks, agency returns, approvals, escalations, and finalizations must require an authorized human actor.
- AI and system actors may recommend, classify, summarize, route, or draft; they must not attest, waive, approve, or finalize.
- Submitted packages must be locked. Later changes must create amendments, returns, or resubmissions.
- Platform support actions must be constrained, visible, permissioned, time-bound where appropriate, and logged.
- Auditors must receive inspectability without mutation rights.

## Functional Requirements

### 1. Organization, Contract, and Workspace Setup

The system must support:

- Agency and nonprofit organizations with independent user management.
- Workspaces by agency, contract portfolio, nonprofit, program, or reporting period.
- Contract setup with budget categories, caps, term dates, funding streams, invoice cadence, and approval workflow.
- Import of existing contract data from spreadsheets, procurement systems, or manual admin entry.
- Versioned contract rules so validations can be reproduced later even after rules change.
- Versioned configuration bundles covering contract setup, schemas, mappings, rules, workflows, templates, and views.
- A sandbox/pilot mode for loading a recent invoice and showing validation without production submission.

Acceptance criteria:

- A contract admin can configure a new contract and invoice template without engineering changes.
- A configuration bundle cannot be activated for production until it is tested and approved by an authorized admin.
- A rule change applies prospectively unless an authorized admin explicitly re-runs validation for existing draft invoices.
- Historical invoices always display the full configuration bundle used at submission time.

### 2. Document and Data Ingestion

The system must ingest nonprofit data in native formats without forcing reformatting.

Supported inputs should include:

- PDF, image, CSV, XLSX, and document uploads.
- Ledger exports from QuickBooks, Sage Intacct, NetSuite, and Blackbaud Financial Edge.
- Payroll/timekeeping exports from ADP, Paychex, and equivalent systems.
- Receipts, vendor invoices, proof of payment, timesheets, and bank records.
- Email-forwarded documents or secure upload links as a later enhancement.

Capabilities:

- Bulk upload with progress, virus scanning, deduplication, and file classification.
- Immutable artifact storage with hash/checksum verification and versioned metadata.
- Document grouping by invoice period, employee, vendor, category, or program.
- OCR and extraction for scanned PDFs/images.
- Structured import for spreadsheets and accounting exports.
- Data lineage from each extracted field back to file, page, bounding box/cell, parser/model version, mapping version, and extraction confidence.
- Manual correction workflow for low-confidence fields, recorded as lineage events rather than destructive edits.

Acceptance criteria:

- A user can upload a mixed package of files and see classified documents within minutes.
- Every extracted amount used in an invoice can be traced back to a source location.
- Duplicate documents are detected before they create duplicate claim lines.

### 3. Invoice Assembly

The system must transform uploaded evidence into a draft invoice package.

Capabilities:

- Map ledger and payroll lines to contract budget categories.
- Group expenses by reporting period and invoice template section.
- Generate invoice header fields, budget summaries, category totals, and backup indexes.
- Support agency-specific invoice templates.
- Preserve original supporting documents while producing a standardized review package.
- Allow user review, correction, exclusion, and annotation of lines before submission.
- Track remaining budget after draft invoice impact.
- Represent draft invoice lines as canonical entities linked to supporting artifacts, source rows, mappings, and validation results.
- Version generated package previews and final packages when they materially change.

Acceptance criteria:

- A nonprofit fiscal user can move from uploaded ledger/backup to draft invoice without line-by-line template entry.
- The draft invoice shows total requested amount, category totals, remaining budget, and unresolved issues.
- Excluded or corrected lines retain reason, actor, and timestamp.
- A generated package can be reproduced from the same invoice, artifact, template, and configuration versions.

### 4. Validation Engine

The validation engine is the product's core. It must evaluate every invoice line and package-level field against contract budgets and agency rules.

Rule types:

- Field completeness.
- Numeric bounds.
- Date eligibility.
- Budget availability.
- Cost allowability.
- Documentation sufficiency.
- Duplicate detection.
- Cross-document consistency.
- Approval workflow completeness.
- Advisory risk indicators for unusual patterns.

Required design properties:

- Deterministic rules for compliance-critical checks.
- Explainable outputs with user-facing reason codes.
- Versioned rules, rule inputs, and configuration context.
- Idempotent validation runs.
- Re-runnable validations after document changes.
- Separation between hard-blocking errors, warnings, and reviewer-visible notes.
- Support for agency-specific configuration without custom code per agency.
- Immutable validation-run records that include invoice version, artifact versions, budget version, schema version, mapping version, rule version, workflow version, template version, and parser/model version where applicable.
- Clear separation between deterministic pass/fail decisions and advisory or AI-assisted signals.

Acceptance criteria:

- A validation result explains what failed, why it failed, what evidence was used, and how to fix it.
- A reviewer can inspect the exact rule and source data behind a flag.
- The system can validate an invoice package repeatedly and produce stable results for the same inputs and configuration versions.
- Advisory risk indicators never create approval, waiver, attestation, or finalization events without explicit human action.

### 5. Real-Time Issue Resolution

The system must let nonprofit users resolve issues before submission.

Capabilities:

- Flag inbox grouped by severity, category, required actor, and invoice line.
- Inline comments and structured responses.
- Replacement document upload tied directly to a flag.
- Re-validation of affected lines only, with full-package validation before final approval.
- Conversation history retained in the validation trace.
- Ability to assign issues to fiscal, program, payroll, or executive staff.
- Issue state changes recorded as events linked to the affected invoice version, line, validation result, and actor.

Acceptance criteria:

- A provider sees all known issues at once rather than receiving serial agency emails.
- Each issue has a status: open, awaiting response, fixed, waived, or accepted risk.
- Waivers require permission, explanation, and audit visibility.
- Accepted risks require an authorized human actor and rationale.

### 6. Nonprofit Approval and Submission

The system must require nonprofit approval before sending an invoice to the agency.

Capabilities:

- Final review screen with invoice totals, validation status, remaining warnings, and generated package preview.
- E-signature or attestation workflow, configurable by agency.
- Lock submitted invoice content against silent mutation.
- Submit via API, procurement-system integration, secure file transfer, email package, or downloadable archive.
- Submission receipt and status tracking.
- Submission package includes immutable references to source artifacts, generated artifacts, validation runs, and configuration versions.

Acceptance criteria:

- After submission, users can view what was submitted but cannot change it without creating an amendment or resubmission.
- The submitted package includes an audit trail and validation summary.
- The nonprofit and agency see the same canonical invoice state.
- Attestation must be performed by an authorized human actor and recorded against the exact submitted invoice version.

### 7. Agency Review Queue

The agency workflow must support fast confirmation while preserving approval authority.

Capabilities:

- Queue by division, reviewer, contract, nonprofit, status, SLA, risk, and amount.
- Invoice detail page with claim summary, validation trace, source evidence, comments, and approval controls.
- Approve, return, request clarification, escalate, or assign actions.
- Review-level workflow such as Level 1, Level 2, treasurer/fiscal final approval, or auditor read-only.
- Bulk triage for low-risk screened invoices with explicit human confirmation and per-invoice decision records.
- Clear distinction between platform-screened status and agency-approved status.

Acceptance criteria:

- Agency users can review flagged items first and navigate from summary to supporting evidence quickly.
- Review decisions are logged with actor, timestamp, role, reason, and affected invoice version.
- Returned invoices carry structured reason codes back to the nonprofit.
- Bulk review actions preserve individual invoice audit events and cannot convert platform-screened status into agency-approved status without authorized approval.

### 8. Status, Reporting, and Analytics

The system must make invoice status transparent to both sides.

Capabilities:

- Real-time status for draft, validating, ready for nonprofit approval, submitted, in agency review, returned, approved, paid, and archived.
- Portfolio dashboards by agency, nonprofit, contract, period, amount, SLA, and status.
- Bottleneck analysis: where invoices wait and why.
- Error analytics: common rule failures, providers needing training, templates causing issues.
- Cash-flow view for nonprofits: submitted, approved, expected payment, aged receivables.
- Exportable data for audit, board reports, and operational review.

Acceptance criteria:

- A nonprofit executive can identify outstanding amount by expected payment status.
- An agency manager can identify reviewers, providers, or rules causing backlog.
- Reports can be exported with filters and consistent definitions.

### 9. Integrations

The system should be useful as a standalone application but designed for integration.

Integration categories:

- Accounting: QuickBooks, Sage Intacct, NetSuite, Blackbaud Financial Edge.
- Payroll/timekeeping: ADP, Paychex, similar providers.
- Procurement/contract systems: agency systems, PASSPort-like portals, ERP/procurement platforms.
- Identity: SSO/SAML/OIDC, MFA, SCIM for larger agencies.
- Storage/export: secure file transfer, agency document repositories, data warehouse export.
- Notifications: email, in-app, and future collaboration tools.

Acceptance criteria:

- Manual upload works before integrations exist.
- Integration imports are traceable and replayable.
- Failed integration jobs do not corrupt invoice state.

### 10. Administration and Configuration

The system must support customer onboarding and rule maintenance without requiring code changes for every contract.

Capabilities:

- Rule authoring interface with templates, test cases, and deterministic execution previews.
- Contract/budget import and mapping tools.
- Invoice-template builder or field mapper.
- Schema registry and mapping registry for customer-specific artifact shapes and canonical fields.
- Workflow, view, and template configuration with versioning.
- Configuration lifecycle management for draft, tested, approved, active, superseded, and retired versions.
- Role and permission management.
- Data retention policies by tenant and contract.
- Support tooling with impersonation safeguards and access logging.
- Feature flags for pilots and agency-specific rollout.

Acceptance criteria:

- An implementation specialist can configure a pilot contract from customer-provided artifacts.
- Rule authors can test rules against historical invoices before activation.
- Production configuration changes require approval, activation timestamp, owner, and test evidence.
- Support access is time-limited, approved, and logged.

## Nonfunctional Requirements

### Security

The product handles sensitive financial, payroll, employee, vendor, and possibly client-adjacent service data. Security requirements should include:

- Tenant isolation at application and data layers.
- Encryption in transit and at rest.
- Strong role-based access control.
- MFA and SSO for agency customers.
- Least-privilege internal access.
- Comprehensive event and provenance logging.
- Malware scanning for uploads.
- Secure secret management.
- Regular vulnerability scanning and penetration testing.
- SOC 2 readiness controls appropriate for sensitive financial, payroll, and public-sector workflow data.

### Privacy and Data Governance

Requirements:

- Data minimization: collect only what is needed for reimbursement validation.
- Field-level handling rules for payroll, bank, tax, employee, and personally identifiable information.
- Configurable retention and deletion policies.
- Legal hold support for audits or investigations.
- Region/state-hosted options where required by public-sector customers.
- Exportability for customer records.
- Retention and deletion workflows that preserve required audit evidence through legal holds, tombstones, immutable hashes, or redacted lineage records where full artifact deletion is legally required.

### Auditability

Auditability is not a secondary feature. It is part of the core product.

Requirements:

- Append-only event log for material actions.
- Actor, role, timestamp, organization, contract, invoice, source IP/session, and reason where applicable.
- Hashing or immutable references for uploaded documents and submitted packages.
- Configuration-version history and validation-run history.
- Reviewable chain of custody from upload to submission to approval.
- Field-level lineage from invoice amount to source artifact, source location, parser/model version, mapping version, validation result, correction history, and submitted package.
- Queryable projections for operational workflows backed by event and lineage records sufficient for reconstruction.

### Reliability

Requirements:

- Durable file storage with checksum validation.
- Idempotent background jobs for extraction, validation, package generation, and submission.
- Recovery from partial failures.
- Clear retry and dead-letter handling for integration jobs.
- Uptime targets appropriate for government business hours, with batch processing outside peak windows.

### Performance

Targets to propose for an MVP:

- Upload acknowledgement in under 5 seconds for normal files.
- Initial document classification visible within 2 minutes for typical invoice packages.
- Validation run for a typical monthly invoice package under 5 minutes.
- Invoice detail page load under 2 seconds for normal package size.
- Support large portfolios through asynchronous processing and pagination.

### Accessibility and Usability

Requirements:

- WCAG 2.1 AA alignment.
- Keyboard navigable review workflows.
- Clear status language for nontechnical users.
- Avoid "black box" AI outputs: show evidence and confidence.
- Support bulk work without hiding critical exceptions.

## AI and Automation Requirements

AI is useful here, but the system cannot rely on unverified model output for compliance-critical decisions.

Appropriate AI uses:

- Document classification.
- OCR cleanup.
- Field extraction.
- Suggested mapping from ledger lines to budget categories.
- Suggested schemas, mappings, validation rules, and extraction plans for implementation specialists.
- Suggested issue summaries.
- Duplicate/similarity detection when results remain explainable and reviewable.
- Reviewer-assist explanations.

Controls:

- Deterministic rule engine remains source of truth for pass/fail validation.
- Confidence thresholds route uncertain extraction to human review.
- Every AI-derived field must be traceable to source evidence.
- Model, prompt, parser, and evaluation version must be recorded for extracted data and AI-assisted configuration.
- Users can correct model output.
- Corrections should feed tenant-appropriate evaluation datasets and, later, fine-tuning or prompt improvements only under approved privacy, consent, and data-governance controls.
- AI-generated configuration cannot affect production validation until reviewed, tested, approved, and versioned.
- AI-generated summaries or recommendations must not create attestations, waivers, approvals, finalizations, or blocking compliance decisions.

Design stance:

- "I would use AI to reduce compilation labor, but not to make opaque approval decisions. The compliance layer should be deterministic, versioned, explainable, and auditable."

## Proposed System Architecture

### High-Level Components

- Web application for nonprofit and agency users.
- API service for workflow, permissions, invoice state, and integrations.
- Document ingestion service.
- OCR/extraction pipeline.
- Validation engine.
- Package generation service.
- Notification service.
- Provenance/event service.
- Configuration registry for schemas, mappings, rules, workflows, views, and templates.
- Reporting/analytics layer.
- Admin/configuration console.

### Suggested Data Stores

- Relational database for tenants, contracts, budgets, invoices, line items, rules, workflow state, and permissions.
- Object storage for uploaded documents and generated packages.
- Append-only event/provenance store for material actions, lineage records, validation runs, and artifact/version references.
- Configuration registry for versioned schemas, mappings, rules, workflows, templates, and views.
- Search index for document metadata, invoice lookup, and audit investigation.
- Warehouse or analytical replica for portfolio reporting.
- Queue system for ingestion, extraction, validation, and integration jobs.

### State Model

Suggested invoice states:

1. Draft
2. Uploading
3. Extracting
4. Needs provider review
5. Validating
6. Issues open
7. Ready for nonprofit approval
8. Approved by nonprofit
9. Submitted to agency
10. In agency review
11. Returned
12. Agency approved
13. Paid
14. Archived
15. Voided/amended

Each transition should be permissioned, logged, and guarded by validation rules.

The state model must represent one canonical invoice lifecycle shared across nonprofit, agency, support, and auditor views. Role-specific screens may project different fields and actions, but they must not create separate stakeholder-specific invoice copies.

## MVP Scope

The strongest MVP is a pilot on one agency division and one contract portfolio, proving value before broad integrations or complex multi-agency rollout.

### MVP Must Have

- Multi-organization accounts: one agency, multiple nonprofits.
- Contract and budget configuration.
- Manual file upload with immutable artifact storage.
- CSV/XLSX ledger import.
- PDF/image document storage and OCR.
- Draft invoice assembly from structured ledger rows.
- Configurable deterministic validation rules.
- Versioned schemas, mappings, rule configuration, template configuration, and workflow state.
- Append-only event log and field-level lineage for claimed amounts.
- Issue resolution workflow.
- Nonprofit final approval.
- Agency review queue.
- PDF/CSV export package with validation summary.
- Complete audit and provenance trail.
- Basic dashboards for invoice status, cycle time, and open issues.

### MVP Can Defer

- Deep native integrations with every accounting/payroll system.
- Fully automated scanned receipt extraction for all formats.
- Advanced advisory risk indicators.
- Cross-agency benchmarking.
- Payment execution.
- Outcome-based contract performance analytics.
- Complex multi-fund allocation optimization.

## Implementation Plan

### Phase 0: Discovery and Domain Modeling

Duration: 2-4 weeks.

Deliverables:

- Map current agency/nonprofit invoice workflow.
- Collect sample contracts, budget sheets, invoice templates, ledgers, payroll exports, and revision emails.
- Create canonical data model.
- Identify top 20 validation rules that cause most returns.
- Define pilot success metrics.

Engineering focus:

- Build a rule taxonomy.
- Separate universal concepts from agency-specific configuration.
- Decide what must be deterministic from day one.

### Phase 1: Pilot Workflow

Duration: 6-10 weeks.

Deliverables:

- Tenant/org/user model.
- Contract setup.
- Upload and document library.
- Ledger import.
- Draft invoice assembly.
- Rule engine v1.
- Flag resolution workflow.
- Agency review queue.
- Export package.
- Audit logging.

Engineering focus:

- Reliable state machine.
- Traceability from line item to source data.
- Idempotent background jobs.
- Simple but solid permissions.

### Phase 2: Extraction and Template Automation

Duration: 6-8 weeks.

Deliverables:

- OCR and structured extraction for common backup docs.
- Invoice template generation.
- Confidence review UI.
- Rule-test harness.
- Improved package preview.

Engineering focus:

- Human-in-the-loop extraction.
- Model/prompt/version tracking.
- Evaluation set from pilot documents.
- Clear fallback when extraction fails.

### Phase 3: Integrations and Scale

Duration: 8-12 weeks.

Deliverables:

- Accounting/payroll import connectors.
- SSO/MFA.
- Procurement-system submission paths.
- Portfolio reporting.
- Admin rule/config console.
- Data retention and export controls.

Engineering focus:

- Integration reliability and observability.
- Tenant-specific configuration at scale.
- Performance on large invoice packages.
- SOC 2 control evidence.

### Phase 4: Intelligence and Optimization

Duration: ongoing.

Deliverables:

- Recurring-error analytics.
- Provider training insights.
- Reviewer workload optimization.
- Advisory risk indicators for unusual claims.
- Predictive payment/cycle-time estimates.

Engineering focus:

- Avoid automating biased or brittle decisions.
- Keep risk models advisory unless they are validated and governed.
- Track precision/recall and false positive cost.

## Key Engineering Risks

### Risk: Rule Complexity Becomes Custom Code

Mitigation:

- Build a rule DSL/configuration model early.
- Start with a small set of composable primitives.
- Keep escape hatches, but measure custom-code requests.

### Risk: AI Extraction Produces Confident Errors

Mitigation:

- Require source trace and confidence.
- Use human review for low-confidence or high-dollar fields.
- Treat extraction as draft data until approved.

### Risk: Audit Requirements Are Added Too Late

Mitigation:

- Design audit logging as a first-class service from the first sprint.
- Record rule version, model version, source file hashes, and user actions.

### Risk: Agency and Nonprofit Incentives Differ

Mitigation:

- Make status transparent to both sides.
- Separate correction workflow from approval authority.
- Ensure returned invoices carry structured reasons, not vague free-text rejection.

### Risk: Integrations Delay MVP

Mitigation:

- Support manual upload and export first.
- Build connector abstractions, but do not block pilot value on native integrations.

### Risk: Security Review Blocks Sales

Mitigation:

- Implement SOC 2-aligned controls early.
- Prepare security documentation, data-flow diagrams, access-control matrix, and incident response process.

## Metrics

### Customer Outcome Metrics

- Median time from nonprofit upload to agency-ready submission.
- Median Level 1 agency review time.
- Number of revision rounds per invoice.
- First-pass acceptance rate.
- Days sales outstanding / reimbursement aging for nonprofits.
- Amount approved and paid by period.
- Percent of invoices with complete validation trace.

### Product Quality Metrics

- Extraction field accuracy.
- Rule false positive rate.
- Rule false negative rate discovered during agency review.
- Percent of flags resolved before submission.
- Time to resolve a flag.
- Duplicate claim detection rate.
- Package generation failure rate.

### Operational Metrics

- Onboarding time per contract.
- Number of rules configured per contract.
- Rule changes per month.
- Support tickets per invoice.
- Processing cost per invoice package.

## Technical POV

Strong framing:

- "The hard part is not generating an invoice. The hard part is encoding institutional review knowledge into a traceable, versioned validation system that both nonprofits and agencies trust."
- "I would draw a hard line between extraction automation and compliance validation. Extraction can be probabilistic; validation needs to be deterministic and explainable."
- "The core data model should revolve around contracts, budgets, invoice lines, source evidence, rules, validation runs, and audit events."
- "The MVP should prove that pre-submission validation reduces revision rounds and agency review time on one contract portfolio before building broad integrations."
- "Auditability is a product feature here, not just an internal compliance concern."

## Discovery Questions

Product/domain:

- Which invoice defects cause the most agency returns today: missing backup, budget overages, wrong category mapping, template formatting, or policy interpretation?
- Is the first buyer usually the agency, the nonprofit, or a combined pilot?
- How much variation exists across agency rules versus common human-services reimbursement patterns?
- What does "screened" mean operationally? Is it a platform confidence status, a deterministic rule pass, or a customer-defined threshold?
- What output format do agencies actually want: API submission, generated PDF, spreadsheet, zip package, or procurement-system upload?

Engineering:

- How are rule versions represented and tested?
- How do you distinguish hard compliance blockers from advisory warnings?
- What guarantees do you provide around audit trails and chain of custody?
- How do you evaluate extraction accuracy on customer documents?
- What is the failure mode when an integration is unavailable near a submission deadline?

Security/compliance:

- Which data classes are in scope: payroll, bank info, SSNs, client service records, HIPAA-adjacent data?
- What hosting or data residency commitments do public-sector customers require?
- What SOC 2 controls have created the most engineering work so far?

Business:

- What is the main ROI proof in pilots: faster payment, fewer revision rounds, lower reviewer workload, audit readiness, or provider satisfaction?
- Who owns rule configuration after onboarding: the platform operator, the agency, or a shared model?
- How do agencies think about automation while preserving human approval authority?

## Recommended Demo Concept

Build or describe a narrow prototype:

- Upload a sample ledger CSV and three supporting PDF/image documents.
- Map expenses to contract budget categories.
- Run five deterministic rules:
  - Date within contract period.
  - Category is allowable.
  - Amount does not exceed remaining budget.
  - Receipt required for vendor expense.
  - Duplicate document/amount/date/vendor warning.
- Show a validation trace for each line.
- Let the nonprofit fix one issue.
- Generate an agency review package.
- Show the agency queue and audit log.

This demonstrates the right instincts: domain modeling, workflow state, rule design, auditability, and practical automation.

## Open Assumptions

- No single public reference architecture is assumed; the architecture here is inferred from the reimbursement workflow problem.
- The exact agency submission mechanism is unknown and likely varies by customer.
- The actual rule corpus is customer-specific; this document proposes representative rule categories.
- Payment execution appears outside the immediate public positioning; approval and reimbursement readiness are in scope, payment initiation may be future scope.
- Pilot-first implementation assumptions are based on the complexity of the workflow and the need to validate configuration against real contracts before scaling.
