# Pilot Implementation Decision Record

Status: Superseded for POC scope

Last updated: 2026-07-11

Controlling Linear project: `Substrate / ContractView`

Linear project status: `Discovery`

## Purpose

Record the product, workflow, governance, and implementation decisions needed to decompose ContractView into implementation-ready Linear projects and issues.

POC scope note (2026-07-11): this pilot-oriented register is retained as background research only. The controlling product-intake artifact for implementation is `docs/product/poc-demo-charter.md`. The POC uses synthetic data and does not require customer validation, real pilot commitments, production operations, or business-outcome measurement.

This is a vendor-neutral reference design for interview and discovery purposes. It does not claim knowledge of any organization's confidential customers, implementation, commitments, or production environment. Named public-sector policies may be used as workflow references, but all customers, providers, volumes, technology choices, and delivery dates below are assumptions until a pilot partner confirms them.

The architectural pillars in `docs/adr/0001-core-architectural-pillars.md` are fixed constraints. Runtime compliance decisions remain deterministic; submitted packages are immutable; stakeholder views share canonical invoice state; audit evidence is durable product data; production configuration requires approval; authority actions require humans; and claimed amounts retain provenance.

## Answer Standard

Each decision records:

- The selected baseline.
- Its status: `Confirmed`, `Pilot assumption`, or `Partially confirmed`.
- What must be validated with a pilot partner.
- The implementation or ticketing consequence.

Assumptions are explicit discovery work, not product fact.

## P0 - Pilot and implementation sequence

### D-01: First pilot customer and buyer

Status: Pilot assumption

Selected baseline:

- Agency-led combined pilot with one large municipal human-services program division.
- Three mid-sized nonprofit service providers and approximately ten active expense-reimbursement contracts.
- Economic buyer and budget owner: agency finance or procurement leadership.
- Agency operational champion: fiscal manager responsible for first-line invoice review.
- Provider champions: controller or CFO plus a grants/accounting specialist at each nonprofit.
- The agency sponsors the shared portfolio. Each provider remains a separate organization and can access only its contracts and evidence.

Validate:

- Actual agency and provider archetypes.
- Agency-procured, nonprofit-procured, or third-party-funded buying model.
- Named economic buyer, budget owner, and operational champions.

Implementation consequence:

- Agency and provider organization tenancy.
- Contract-scoped provider access and agency portfolio visibility.
- Hard prohibition on cross-provider evidence access.
- Pilot analytics across the selected portfolio.

### D-02: Exact reimbursement workflow

Status: Pilot assumption

Selected baseline:

- Monthly, expense-based human-services reimbursement.
- One program division, three providers, ten contracts, and roughly ten new invoices monthly.
- Up to fifteen monthly packages when returns, replacements, deductions, and late submissions are included.
- Typical invoice: 200-500 ledger lines, 5-15 budget categories, 10-30 files, 50-300 pages, and 20-75 MB.
- Pilot maximum: 2,500 lines, 100 files, 1,500 pages, and 300 MB.

Workflow:

1. Provider closes its books.
2. Finance exports the contract ledger and payroll data.
3. Staff collect supporting evidence.
4. Expenses are mapped to agency budget categories.
5. Required worksheets are prepared.
6. A provider approver reviews and attests.
7. The immutable package is exported for manual submission to the agency's procurement portal.
8. Agency first-line staff review completeness, period, category, and budget alignment.
9. A supervisor performs second-line review.
10. Returned invoices are corrected through a new revision and resubmitted.
11. Authorized payment staff record later payment states.

Validate:

- At least six months of p50, p95, and maximum package sizes.
- Actual state names, review layers, systems, and handoffs.
- Whether payment-status tracking is supplied manually or imported.

Implementation consequence:

- Benchmark fixtures at typical, p95, and maximum size.
- Vertical workflow slices for import, evidence, mapping, resolution, attestation/export, agency review, and revision.

### D-03: Pilot success outcome

Status: Pilot assumption

Primary metric:

> At least 90% of submitted invoices pass first-line agency review without return for a preventable documentation, reconciliation, formatting, service-period, or budget-rule error.

Baseline and classification:

- Analyze the prior six months for the selected contracts.
- Classify returns as platform-preventable, judgment-dependent, external-system, incomplete-source, or post-submission policy/budget change.
- Only platform-preventable returns count toward the intervention metric.

Guardrails:

- Zero unauthorized submissions, approvals, or waivers.
- Zero known deterministic blockers presented as passed.
- 100% of claimed amounts traceable to evidence and mapping decisions.
- Median time from complete upload to provider-reviewable package under 15 minutes.
- Median active provider labor under two hours per invoice.
- At least 95% of critical extracted monetary fields accepted without correction.
- Zero cross-provider data exposure.

Sample and acceptance:

- Historical backtest of at least 100 invoice packages.
- Twelve-week live pilot with at least 30 submitted invoices and two cycles per provider.
- Joint acceptance by agency fiscal leadership, the agency operational champion, and one controller/CFO per provider.

Validate:

- Feasibility of the historical and live sample sizes.
- Existing baseline and partner-approved reason taxonomy.
- Whether first-pass acceptance is the primary economic outcome.

Implementation consequence:

- Define the pilot-metrics event model before dashboard implementation.
- Record timestamps and reason codes for every material stage, finding, correction, submission, return, and approval.

### D-04: Mandatory source artifacts

Status: Pilot assumption

Selected baseline:

- CSV/XLSX general-ledger exports.
- CSV/XLSX payroll registers.
- Agency budget and purchase-order exports.
- Agency invoice templates, personnel worksheets, and conditional equipment worksheets.
- Searchable and scanned PDF, JPEG, PNG, and DOCX that can be deterministically normalized.
- Contract ledger, payroll register, personnel worksheet, receipts/vendor invoices, proof of payment, applicable rent/equipment evidence, relevant timesheets, and budget/purchase-order snapshot.
- Payroll is in scope. Arbitrary automated timesheet interpretation is not.
- Assume 80% digitally generated and 20% scanned documents. Handwriting requires human review.
- Password-protected or corrupt files are rejected with a stable reason code.

Evaluation data baseline:

- Six months of historical packages, final outcomes, return comments, approved budgets, and tenant-limited permission for testing and evaluation.

Validate:

- Actual source schemas and mandatory evidence by expense class.
- Presence of bank, tax, or client-adjacent evidence and required redaction.
- Rights to retain and evaluate historical packages.

Implementation consequence:

- File validation, malware scanning, immutable originals, normalized renderings, page/row provenance, schema parsers, human review queue, and sanitized fixtures.

### D-05: Produced package and delivery

Status: Pilot assumption

Selected baseline:

An immutable package version contains:

1. Agency invoice workbook.
2. Rendered invoice PDF.
3. Personnel worksheet.
4. Supporting documents in original formats.
5. Validation summary PDF.
6. Evidence manifest CSV.
7. Machine-readable manifest JSON.
8. SHA-256 hashes for all included files.
9. One deterministically ordered ZIP export.

The manifest includes package version, contract and purchase-order identifiers, service period, expense-line identifier, claimed amount, category, source and location, extraction/mapping provenance, validation result, and disposition.

The pilot ends at human-approved download/export and manual submission into the external procurement portal. Direct submission is deferred until a supported, authenticated integration is contractually authorized.

An authorized provider approver personally accepts the configured attestation. ContractView records actor, timestamp, package hash, and attestation-text version; it never attests for the user.

Default naming convention:

`{agency}_{provider}_{contract}_{service-period}_{invoice-id}_v{revision}`

Validate:

- Exact agency templates, certifications, file order, size constraints, naming, and accessibility requirements.
- Whether any direct submission has been promised.

Implementation consequence:

- Template renderer, PDF and manifest generation, deterministic ZIP, hashing, attestation ceremony, export event, and package reproduction tests.

### D-06: Deterministic validation rules and severity

Status: Pilot assumption

Blockers:

1. Contract, budget, or purchase order is missing or inactive.
2. Service period is outside the valid contract or fiscal period.
3. Mandatory evidence is absent.
4. Invoice totals do not reconcile to component lines.
5. Claim exceeds available category or contract budget.
6. Ledger expense lacks an invoice-category mapping.
7. Required payroll data does not reconcile to the personnel claim.
8. Exact duplicate invoice or expense is detected.
9. Expense date is outside the service period.
10. Provider attestation is absent.
11. An active budget modification prohibits submission against the affected budget.

Warnings:

1. Probable duplicate.
2. Low-confidence extraction.
3. Unusually front-loaded spend.
4. Category approaching exhaustion.
5. Incomplete allocation support.
6. Weak or obscured proof of payment.
7. Material recurring-cost variance.
8. Illegible evidence that is not mandatory for initial review.

Informational findings:

1. Remaining balances.
2. Deadline proximity.
3. Optional evidence absent.
4. Material month-over-month variance.
5. Historical return frequency for the rule.

Authority and conflicts:

- Provider users may correct data or replace evidence.
- Providers may explain warnings but cannot waive agency policy.
- Authorized agency policy owners may accept configured warnings.
- A blocker is waivable only through an explicit configured agency exception path.
- Every exception records actor, reason, and policy basis.
- Conflicting rules block configuration activation; runtime never silently chooses.
- Missing mandatory, conditional, and optional evidence produces a blocker, warning, and informational finding respectively.

Validate:

- Top return causes and exact rule inputs, reason codes, severities, and exception authority.
- Whether every listed warning is sufficiently deterministic to calculate.

Implementation consequence:

- Versioned rule schema, stable reason-code registry, pure deterministic evaluator, finding lifecycle, waiver records, and executable policy tests.

### D-07: Invoice workflow and authority matrix

Status: Pilot assumption

Canonical states:

`Draft` -> `Processing` -> `Provider Review Required` -> `Ready for Attestation` -> `Submitted` -> `Agency Level 1 Review` -> `Agency Level 2 Review` -> `Payment Review` -> `OK to Pay` -> `Disbursed`

Branch states:

- `Returned`
- `Withdrawn`
- `Canceled`
- `Superseded`
- `Voided`
- `Processing Failed`

Authority:

- Provider preparer: upload, classify, map, resolve, and preview; no attestation unless separately granted approver authority.
- Provider approver: final review, attestation, export/submission, and policy-permitted withdrawal. One approver is sufficient for MVP.
- Agency Level 1 analyst: review, clarify, return, and recommend progression; no final approval or payment authority.
- Agency Level 2 supervisor: approve, return, accept permitted warnings, and exercise configured exception authority.
- Payment analyst/finance director: record authorized payment-review, OK-to-pay, and disbursement states.
- Auditor: scoped read and export only.
- Platform support: no attestation, submission, return, waiver, approval, or payment authority.

A submitted package is never edited. A return creates a draft revision that references it. Resubmission creates a new package version and hash. Cancellation is terminal; later work uses a new invoice or revision.

Validate:

- Exact external-system states and transition authority.
- Segregation-of-duties and multi-approver requirements.
- Withdrawal, cancellation, and payment-state synchronization.

Implementation consequence:

- Explicit transition registry with role checks, invariants, idempotency keys, and domain events.

### D-08: Configuration ownership and activation

Status: Pilot assumption

Selected baseline:

- Platform implementation staff draft schemas, mappings, templates, and rules from partner artifacts.
- Provider finance staff help define source-system mappings.
- Agency fiscal-policy staff own rule meaning, severity, exception policy, workflow, and outputs.
- Bundles require schema validation, deterministic rule tests, historical replay, template golden tests, authorization checks, and partner acceptance testing.
- Provider controller approves provider mappings.
- Agency fiscal-policy owner approves agency rules, workflow, and templates.
- Platform engineering confirms technical validity but cannot approve policy meaning.
- MVP uses controlled configuration-as-data tooling, not a general-purpose customer rule builder.
- Bundles are immutable, versioned, effective-dated, approved, tenant/portfolio-targeted, and linked to every evaluation and submission.
- Rollback activates a prior approved bundle prospectively; it never rewrites history.
- Emergency activation requires both platform authority and a named agency approver.
- Shared base rules may be copied as templates, but tenant versions never change silently.

Validate:

- Actual staffing and approval authority.
- Required partner self-service in the pilot.
- Emergency-change and rollback expectations.

Implementation consequence:

- Configuration registry, review workflow, semantic diff, replay harness, staged activation, rollback, and immutable bundle references.

## P1 - Sensitive data and platform decisions

### D-09: Sensitive-data scope

Status: Pilot assumption

Permitted when required:

- Employee name or internal ID, position, pay date/amount, allocated hours/percentage, vendor, expense/payment details, masked payment evidence, contract identifiers, and pseudonymous client case ID only when unavoidable.

Prohibited in the pilot:

- Full SSNs, full bank/routing numbers, unredacted tax documents, home addresses, birth dates, health records, client narratives, direct service-recipient identifiers, and authentication secrets.

Documents with prohibited data must be rejected or redacted before acceptance.

Retention and residency baseline:

- Six years after the applicable final-payment, expiration, or termination milestone, unless policy or legal hold requires longer.
- Export before scheduled deletion.
- Audit metadata and package hashes follow the approved retention schedule.
- United States data residency with primary and backup regions in-country.

AI-data baseline:

- No training of general models with customer data.
- No cross-tenant training corpus.
- Providers must disable training and unnecessary retention contractually.
- Tenant-authorized evaluation stays tenant-scoped.
- Broader improvement requires written authorization and de-identification.

Validate:

- Contractual data classes, redaction, retention trigger, legal hold, residency, export, and AI-processing terms.

Implementation consequence:

- Minimization, redaction, retention policies, legal hold, export, regional controls, and AI-provider data constraints.

### D-10: Identity, access, and support access

Status: Pilot assumption

Selected baseline:

- Managed identity provider with password/passwordless login, mandatory MFA, recovery codes, session timeout, and risk-based lockout.
- SAML/OIDC SSO is a later requirement unless required for launch.
- Agency admins invite and role agency users.
- Provider admins control their own users and authority.
- Agency admins associate providers with contracts but do not grant internal provider authority.
- Provider roles: administrator, preparer, approver, read-only.
- Agency roles: program officer, finance analyst, supervisor, auditor, read-only.
- No invisible impersonation.
- Support access requires a customer-approved ticket or declared emergency, named operator, purpose, scope, expiry, read-only default, and prominent audit event.
- Support write access requires explicit approval and never permits human-authority actions.
- Auditors see assigned contracts, immutable packages, findings, configuration, events, and approved exports only.

Validate:

- Launch SSO requirement, session policy, role vocabulary, support approval, and auditor scope.

Implementation consequence:

- Central authorization, tenant-scoped queries, MFA, time-bound support grants, session metadata, and authorization regression tests.

### D-11: AI-assisted MVP behavior

Status: Pilot assumption

In scope:

- OCR, classification, table/field extraction, mapping suggestions, evidence matching, explanations of deterministic findings, and missing-document suggestions.

Prohibited authority:

- AI cannot determine compliance, waive, attest, submit, approve, return, or mark paid.

Evaluation baseline:

- Auto-populate a critical field only when held-out precision is at least 99.5%; otherwise require human review.
- Deterministically reconcile monetary totals, service periods, contract IDs, and budget categories.
- Critical monetary precision at least 99.5% and recall at least 98%.
- Classification macro F1 at least 98%.
- Expense-to-source linkage precision at least 99%.
- Report by document class and scan quality.

Technology baseline:

- Use provider-neutral OCR and enterprise LLM interfaces.
- A managed-cloud OCR/LLM stack is a replaceable pilot assumption, not a known organizational decision.
- Prompts contain only the data required for the extraction task.

Fallback:

- Preserve uploads, allow manual classification/import/entry, continue deterministic validation and package generation, and never submit automatically after recovery.

Validate:

- Existing providers and architecture.
- Evaluation dataset and any externally claimed accuracy methodology.
- Per-field thresholds and manual-review capacity.

Implementation consequence:

- Evaluation sets, field provenance, review queues, model/prompt versioning, adapters, circuit breakers, and manual fallback.

### D-12: Corrections, duplicates, allocations, and rounding

Status: Pilot assumption

Selected baseline:

- Draft structured data is editable with durable history; original files are immutable.
- Submitted corrections create linked revisions and require a reason.
- Exact duplicate identity uses provider, contract, period, source invoice, vendor, date, amount, file hash, and normalized line fingerprint.
- Exact duplicates block. Probable duplicates warn and may be dismissed with reason. Exact overrides require agency authority.
- One expense may split across budget lines within the same contract and service period.
- Splits record source amount, method, percentage/amount, destinations, actor, and evidence.
- Cross-contract, cross-provider, and cross-fund allocation is excluded.
- USD only, decimal arithmetic, two decimals, and round half away from zero at final allocated-line boundaries.
- Residual assignment is deterministic and recorded; allocations must exactly reconcile.
- Corrections to prior submissions use linked adjustments. Reversals never delete the original claim.
- Free-form negative lines and carry-forward balances are excluded.

Validate:

- Duplicate identity, rounding convention, exact-override authority, and required adjustment form.

Implementation consequence:

- Revision lineage, fingerprints, allocation entities, money primitives, adjustment packages, and property-based reconciliation tests.

### D-13: Budget-control semantics

Status: Pilot assumption

Selected baseline:

- Authoritative budget is a versioned snapshot imported from the agency's financial/procurement system.
- `available = active approved budget - approved/disbursed claims - submitted pending claims - active submission reservations`.
- Drafts forecast but do not reserve.
- Provider-approved submission creates a reservation atomically with its state transition.
- Concurrent submissions against one budget line are serialized.
- Returned invoices retain reservations until withdrawal, cancellation/void, explicit agency release, or atomic supersession.
- Budgets are immutable and effective-dated by version.
- Drafts revalidate against the newest active budget; submitted invoices retain their submission snapshot.
- Budget changes may temporarily block new submissions.
- Budget modifications occur in the authoritative external system and import as new versions.

Validate:

- Actual budget source, approved/paid/pending accounting, reservation policy, concurrency, and amendment effects.

Implementation consequence:

- Budget snapshots, reservations, transaction locks, amendment states, modification blockers, and external reconciliation.

### D-14: Notifications and deadlines

Status: Pilot assumption

Selected baseline:

- In-app and email only.
- Notify on upload rejection, processing completion/failure, human-review requirement, attestation readiness, export, clarification, return, resubmission, approval, payment states, deadline proximity, configuration activation, and support access.
- Deadline precedence: contract terms, agency policy, program guidance, agency default, pilot default.
- Store UTC timestamps with configured local timezone, business calendar, and daylight-saving semantics.
- Remind five and two business days before, on the due date, and daily while overdue; escalate after two overdue business days.
- Quiet hours 7 p.m.-8 a.m. local except same-day deadline and security events.
- Delivery logs are operational telemetry unless a configured policy promotes formal notice to durable evidence.

Validate:

- Actual deadline rules, channels, escalation, timezone/calendar, and formal-notice requirements.

Implementation consequence:

- Deadline calculation, calendars, templates, preferences, escalation, and separation of delivery telemetry from audit authority.

## P2 - Platform and delivery planning

### D-15: Implementation and hosting constraints

Status: Pilot assumption

Application baseline:

- React/TypeScript web application.
- FastAPI modular monolith and Python background workers.
- PostgreSQL canonical transactional store.
- Immutable object storage and queue-based asynchronous processing.
- Avoid premature microservices and Kubernetes.

Cloud baseline:

- Managed containers, PostgreSQL, object storage, queues/dead-letter queues, key management, secrets, WAF/CDN, logs/metrics/traces, and provider-neutral OCR/LLM adapters.
- United States primary region with a documented regional-isolation path.

Environments and delivery:

- Local synthetic fixtures, CI test, redacted sandbox/demo, dedicated pilot, and production.
- Pilot and production isolation; production data never enters lower environments.
- Infrastructure as code, container deployment, reviewed migrations, pull-request changes, rolling/blue-green delivery, and health-check rollback.

Validate:

- Existing application and infrastructure inventory before proposing change.
- Mandated cloud, identity, OCR/LLM, deployment, and infrastructure-as-code tools.
- Whether this is hardening an existing system or building a new one.

Implementation consequence:

- Inventory and gap assessment precede stack-change tickets.
- Introduce infrastructure only where current capabilities cannot meet pilot security, auditability, or workload requirements.

### D-16: Reliability and operational targets

Status: Pilot assumption

Selected baseline:

- 99.5% monthly availability during 7 a.m.-9 p.m. local business days, with increased month-end coverage.
- PostgreSQL RPO 15 minutes and RTO four hours; point-in-time recovery, object integrity inventory, and quarterly restore exercise.
- Upload acknowledgement p95 under two seconds excluding transfer.
- Typical extraction p95 under 15 minutes; maximum pilot package under 60 minutes or visibly delayed.
- Structured revalidation p95 under 30 seconds; package generation p95 under five minutes; normal agency queue p95 under two seconds.
- Idempotent jobs, exponential backoff, at most five automated attempts, dead-letter queue, reasoned operator replay, visible status, retained partial success, and no duplicate publication.
- Deadline failure preserves upload time, alerts the user, offers manual/raw fallback, and never claims or performs submission.
- Monitor queue health, processing latency, provider errors, rule failures, package failures, authorization signals, confidence, first-pass acceptance, and recovery health.

Validate:

- Business hours, SLOs, recovery objectives, maximum processing latency, incident ownership, and communication obligations.

Implementation consequence:

- SLOs, alerts, runbooks, replay tooling, restore verification, incident severity, and communication templates.

### D-17: Accessibility, browsers, devices, and localization

Status: Pilot assumption

Selected baseline:

- WCAG 2.2 AA for pilot workflows and generated user-facing documents.
- CI automation plus keyboard, screen-reader, zoom, contrast, table, focus, labeling, tagged-PDF, and accessible-workbook testing.
- Latest two major versions of Chrome, Edge, Firefox, and Safari.
- Desktop for creation/review, tablet for review/approval, mobile for status and limited review.
- Dense mobile editing and native mobile application excluded.
- English, USD, US date display, configurable local timezone, internal ISO dates, and UTC timestamps.
- Data model remains locale-aware; translation and multicurrency are deferred.

Validate:

- Contractual accessibility standard, assistive-technology test matrix, browser policy, and tablet approval expectations.

Implementation consequence:

- Accessibility criteria belong in each affected delivery issue and certification journey.

### D-18: Explicit pilot exclusions

Status: Pilot assumption

Out of scope:

- Direct procurement-portal submission.
- Payment initiation.
- Procurement, solicitation, award, contract creation, and registration.
- Budget-modification authoring.
- Performance/milestone/rate-based reimbursement.
- Cross-contract/provider allocation.
- Multicurrency, full tax processing, prohibited personal data, fraud determinations, autonomous compliance or authority actions, customer rule-builder, general report-builder, native mobile, multilingual UI, full historical migration, automated handwriting recognition, broad native integrations, and SSO unless contractually required.

Operational handling:

- Excluded cases receive an `UnsupportedCase` reason, route to manual processing, retain permitted evidence, are never silently dropped, and are reported separately from product failures.

Validate:

- Confirm every exclusion, especially direct submission, contract types, SSO, integrations, and migration.

Implementation consequence:

- Explicit unsupported-case disposition and taxonomy.

### D-19: Implementation slicing and release

Status: Pilot assumption

Milestones:

1. Pilot certification inputs: data terms, named contracts, historical packages, rule corpus, schemas, templates, baseline, and sensitive-data inventory.
2. Secure canonical foundation: tenancy, identity/MFA, RBAC, budgets, immutable evidence, revision model, and audit events.
3. Ingest and review: upload, scanning, OCR, classification, extraction, provenance, and correction.
4. Deterministic validation: rules, findings, reason codes, resolution, replay, and reservations.
5. Approval and package export: provider review, attestation, immutable package, manifest, hashes, export, and revision.
6. Agency workflow and operations: queue, return/clarification, review layers, auditor view, notifications, metrics, and runbooks.

Release baseline:

- Historical canary against 100 packages.
- Start live use with one provider and two contracts.
- Expand after two accepted invoices.
- Measure for twelve weeks.
- Use tenant flags, contract configuration targeting, replay before activation, one-provider canary, prospective configuration rollback, safe application deployment, backward-compatible migrations, and immutable submitted packages.

Team baseline:

- Product/domain lead.
- Full-stack technical lead.
- Part-time implementation/domain analyst.
- Part-time security/compliance support.
- Design support as needed.

Validate:

- Actual team, existing-system maturity, committed dates, partner onboarding capacity, and required milestone order.

Linear consequence:

- Use outcome-oriented milestone projects and vertical issues rather than frontend/backend/AI/infrastructure silos.

## Working Exercise Defaults for Unconfirmed Inputs

The following defaults remove ambiguity for user-story creation. They are not customer commitments. Each affected epic must retain a discovery or validation story so a real partner answer can replace the default without being mistaken for scope change.

DISC-01 exercise disposition (2026-07-11): E-01 through E-04 are explicitly accepted as the implementation-exercise baseline. This resolves ambiguity for backlog design but does not convert the defaults into verified customer facts. External confirmation remains tracked in `docs/product/discovery/disc-01-pilot-workflow-validation.md` and Linear issue `SUB-24`.

### E-01: Customer archetype

Working default:

- One large US municipal human-services agency division.
- Three mid-sized nonprofit providers.
- Ten active monthly expense-reimbursement contracts.
- The reference program funds residential or shelter-like services, producing payroll, rent, equipment, vendor, and allocated-personnel evidence.

Illustrative public example:

- A New York City-style human-services reimbursement portfolio is the process model because public municipal guidance describes approved budgets, expense-based invoices, supporting-document review, provider certification, and layered agency review.
- This identifies a workflow archetype, not a real customer or prospect.

User-story rule:

- Write personas as `Agency Fiscal Analyst`, `Agency Fiscal Supervisor`, `Provider Preparer`, `Provider Approver`, `Auditor`, and `Platform Implementation Specialist`.
- Do not use a real agency or provider name in stories, fixtures, screenshots, or seed data.

### E-02: Buyer and operating model

Working default:

- Agency-led combined pilot.
- Agency finance/procurement leadership is the economic buyer and portfolio sponsor.
- Providers receive access as participating organizations rather than purchasing separate deployments.
- Agency sees portfolio-level status and aggregate metrics; providers see only their own contracts, invoices, users, and evidence.
- Platform staff onboard the first agency and providers through controlled administration.

Best-guess rationale:

- Agency sponsorship gives one party authority to define rules, outputs, review workflow, and success criteria while preserving each provider's organizational boundary.

User-story rule:

- Treat agency-defined configuration as authoritative only after named human approval.
- Never infer that agency sponsorship permits agency users to administer internal provider authority or view evidence outside assigned contracts.

### E-03: Contract type, volume, and package profile

Working default:

- Monthly expense reimbursement against an approved contract budget and budget categories.
- Ten new invoices per month; up to fifteen packages including revisions and late submissions.
- Typical: 350 ledger lines, 10 budget categories, 20 files, 150 pages, and 50 MB.
- Large acceptance fixture: 2,500 lines, 100 files, 1,500 pages, and 300 MB.
- Source mix: 80% digital, 20% scanned.
- USD, one contract, one service month, and one provider per invoice.

Illustrative public example:

- The workflow resembles a municipal procurement portal in which an active budget/purchase-order record precedes invoice preparation, evidence upload, provider certification, agency review, and payment processing.

User-story rule:

- Every ingestion, processing, review, and export epic must include typical and large-fixture acceptance scenarios.
- Cross-contract, cross-provider, cross-fund, rate-based, and milestone-based reimbursement remain unsupported cases.

### E-04: Submission boundary

Working default:

- ContractView stops at human-approved, immutable package export.
- An authorized provider user manually submits the exported files through the external procurement portal.
- ContractView records export, attestation, hashes, and package manifest but does not claim external submission occurred.
- Agency users may record or import the external submission identifier and later status.
- Direct API or robotic portal submission is out of scope.

Best-guess rationale:

- Manual handoff avoids inventing an integration contract, credentials model, portal automation policy, or legal authority that has not been confirmed.

User-story rule:

- Separate `Ready for export`, `Exported`, and externally confirmed `Submitted` events.
- Never transition to `Submitted` merely because a ZIP was generated or downloaded.

### E-05: Existing platform and technology baseline

Working default:

- Treat the exercise as a new modular-monolith implementation, while making the first delivery story an inventory/gap check that can redirect work if an existing system is discovered.
- React and TypeScript web application.
- Python/FastAPI API and background workers.
- PostgreSQL canonical transactional store.
- S3-compatible immutable object storage.
- Managed queue with dead-letter handling.
- Provider-neutral interfaces for OCR, LLM, email, identity, and object storage.
- Managed container deployment; no Kubernetes or service decomposition in the pilot.
- Infrastructure as code and reviewed database migrations.

Best-guess deployment:

- Separate local, CI, demo/sandbox, pilot, and production environments.
- Pilot and production data isolation.
- US-region managed cloud services with encryption through managed keys and secrets.

User-story rule:

- Express stories in capabilities and contracts rather than vendor services unless an infrastructure story specifically implements the replaceable adapter.
- Create an ADR review item before changing the modular-monolith or canonical-store assumption.

### E-06: Sensitive-data and contractual boundary

Working default:

- Permit minimum employee/payroll, vendor, expense, contract, and masked payment data required to substantiate a claim.
- Reject or require redaction of full SSNs, full bank details, tax returns, dates of birth, health records, client narratives, direct service-recipient identifiers, and credentials.
- US-only storage and processing.
- Six-year retention after the applicable final-payment/contract milestone, with legal hold and export-before-deletion.
- No general-model training, cross-tenant learning, or secondary use without written authorization.
- Mandatory MFA; least privilege; no invisible support impersonation.

Illustrative public example:

- Municipal reimbursement guidance commonly requires payroll and proof-of-payment evidence and multi-year retention, making data minimization and redaction first-class workflow requirements rather than later security enhancements.

User-story rule:

- Use synthetic data in development and demos.
- Any new artifact class or data field triggers security/privacy review before implementation leaves design review.
- Retention deletion must preserve legal holds and never break submitted-package reconstruction.

### E-07: Historical evaluation dataset and quality methodology

Working default:

- Create a synthetic seed corpus immediately and plan for a partner-authorized historical corpus of 100 packages spanning at least six months.
- Split historical data by package, never by page or line, into development, calibration, and held-out test sets.
- Preserve document class, scan quality, provider, and time-period strata.
- Critical monetary fields target at least 99.5% precision and 98% recall.
- Document classification targets at least 98% macro F1.
- Expense-to-source linkage targets at least 99% precision.
- First-line preventable-return detection is evaluated separately from extraction metrics.
- Human corrections, abstentions, unsupported cases, and low-confidence routing count explicitly.

Best-guess governance:

- A domain reviewer approves labels and adjudicates disagreements.
- Dataset versions, annotation policy, model, prompt, parser, thresholds, and results are immutable release evidence.
- No claimed accuracy is accepted without a reproducible denominator, sampling method, and held-out result.

User-story rule:

- AI-assisted capabilities require an evaluation story and human-review fallback before their implementation story can be accepted.
- Deterministic rule correctness uses executable fixtures and historical replay, not model-quality metrics.

### E-08: Team, timing, and rollout

Working default:

- Twelve-week build/hardening exercise followed by a twelve-week measured pilot.
- Core team: one product/domain lead, one senior full-stack technical lead, one additional full-stack engineer, part-time implementation/domain analysis, part-time security/compliance, and design support.
- Two-week milestone zero for data terms, sample acquisition, rule corpus, templates, workflow confirmation, threat-model inputs, and baseline measurement.
- Five demonstrable delivery slices after milestone zero: secure foundation; ingest/review; deterministic validation; approval/export; agency workflow/operations.
- Historical canary against 100 packages, then one provider/two contracts, then expansion after two accepted invoices.

Best-guess planning rule:

- Dates are planning assumptions rather than commitments.
- Scope flexes before provenance, deterministic validation, human authority, tenancy isolation, or immutable submission guarantees.

User-story rule:

- Organize Linear work by vertical user outcome.
- Each story includes actor, preconditions, happy path, failure behavior, provenance evidence, authorization, deterministic acceptance criteria, and affected journey.
- Mark external-data, partner-policy, and infrastructure-inventory dependencies explicitly.

## Remaining Confirmation Register

The exercise defaults above are sufficient for story creation. These remain partner-validation items, not blockers to drafting:

1. Actual customer and provider archetypes.
2. Buying and sponsorship model.
3. Contract types, workflow, volumes, and package distributions.
4. Direct-submission commitments.
5. Existing platform and infrastructure inventory.
6. Contractual data, retention, residency, and AI-processing terms.
7. Historical evaluation corpus and any existing accuracy methodology.
8. Delivery team, onboarding capacity, and committed date.

## Ticket-Creation Readiness

The register now supports complete exercise-level user-story drafting and provisional milestone creation. Stories must label unconfirmed customer facts as exercise defaults and include validation dependencies. Customer-specific commitments should not be presented as settled until the applicable partner confirmation above is recorded.
