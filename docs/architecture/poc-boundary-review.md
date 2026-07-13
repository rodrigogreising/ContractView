# POC Boundary Review

Status: Journey 11 POC baseline certified; SUB-74 successor MVP design review
active

SUB-59 design amendment: the runtime is governed by the
[enforceable modular monolith](modular-monolith.md) and
`modular-monolith-policy.json`. SUB-61 implements the shared ontology and
SUB-62 implements physical module/persistence enforcement. SUB-66 recertified
the merged recovery baseline, and SUB-55 subsequently certified terminal
Journey 11. This document now preserves that POC boundary while SUB-74 reviews
the separately scoped successor MVP.

## Runtime Shape

The POC is one modular application deployed as web, API, worker, PostgreSQL, and MinIO processes. Logical ownership remains explicit.

| Module | Owns | Emits | Must not do |
| --- | --- | --- | --- |
| Web app | Role-aware views, forms, Playwright selectors | Authenticated commands | Authorize only in UI, mutate canonical state directly |
| Identity/RBAC | Seeded users, password hashes, sessions, role/resource policies | Login, logout, denial events | Provide role editor, bypass resource scope |
| Configuration | Draft and immutable active versions | Config activated | Mutate active versions, create generic no-code rules |
| Ingestion | Upload registration, hashes, import jobs | Artifact registered, job queued | Decide compliance |
| Extraction worker | Ledger parsing, OCR/LLM draft fields | Extraction drafted/failed | Create pass/fail or authority decisions |
| Invoice/workflow | Invoice versions, states, human commands | Correction, attestation, submission, return, approval | Mutate submitted versions |
| Validation | Deterministic rules and runs | Finding produced | Use runtime AI as rule truth |
| Package generation | PDF, manifest, ZIP, hashes | Package generated | Fill missing data with AI, mutate packages |
| Provenance/audit | Append-only events and lineage queries | Audit export queried | Rely only on application logs |

## Allowed Dependencies

- Web depends on API contracts only.
- API modules depend on shared domain/config/event/rule contracts and persistence interfaces.
- Worker consumes versioned jobs and writes draft extraction results through owned application services.
- Validation consumes explicit invoice, artifact, budget, and configuration snapshots.
- Package generation consumes an attested invoice version and approved template settings.
- Audit queries read event/lineage records and immutable artifact references.

No module imports another module's private implementation or writes another owner's tables directly.

All modules use the domain -> application <- adapter direction. Repository and
unit-of-work ports are application-owned. Direct SQL is confined to an owner
persistence adapter; cross-capability SQL, shared mutable ORM models, and
connection escape hatches are forbidden. HTTP and worker entry points invoke
application commands and never own business rules.

## Configuration And Runtime Split

Configuration definitions become immutable versions through governance.
Runtime invoice, validation, package, workflow, and provenance records refer to
those exact versions. Draft editing never mutates an activated configuration;
activation, re-validation, package generation, return, and resubmission create
new versioned records prospectively.

## Deterministic And Human Boundaries

- Server-side policies protect every material command.
- AI drafts fields only.
- Rules decide blockers/warnings deterministically.
- NGO Approver alone attests/submits.
- Government Reviewer alone returns/approves.
- Auditor is read-only.

## Build Gate

Boundary tests must cover dependency rules, forbidden direct writes, server authorization, version locks, AI authority prohibition, and audit reconstruction.

## Implemented Authorization Contract

`services/api-workflow/app/domain/authorization.py` is the reusable server-side
policy boundary. It evaluates actor, organization, persona role, resource kind,
agency/NGO scope, submission visibility, publication visibility, explicit
privileged assignment, canonical-scope evidence, and requested action before a
command can mutate state. Session transport is deliberately separate;
test-only identity injection is prohibited. The former flat path is a
compatibility export only.

SUB-60 adds `services/api-workflow/app/application/commands/access_scope.py` as the only application
scope-construction boundary. It resolves contract ownership, invoice state,
artifact publication, extraction/job linkage, government queue linkage, and
administrator/auditor assignments from PostgreSQL. Hand-built or caller-derived
scopes fail closed. Configuration administrators are contract/agency assigned;
auditors are contract assigned, read-only, and limited to submitted evidence.

| Boundary property | SUB-60 declaration |
| --- | --- |
| Owner role | Identity/RBAC capability; security owner reviews policy evidence |
| Responsibilities | Canonical scope resolution, explicit privileged assignment, role/resource/action decision, pre-mutation denial |
| Data owned | `users`, sessions, and `contract_role_assignments`; contracts and resource lifecycle are read through declared authorization queries and remain owned by their capabilities |
| Allowed dependencies | Authorization domain vocabulary, application-owned query ports, and declared read-model adapters |
| Events emitted | No new runtime event; retained machine-readable test/PR evidence proves denials and assignment behavior |
| Configuration consumed | Seeded synthetic contract-role assignments only; no runtime AI or generic policy editor |
| Deterministic requirements | Same canonical actor, assignment, resource state, kind, and action always return the same decision |
| Human authority boundary | Assignments do not grant attestation, submission, return, approval, waiver, or activation beyond the existing named roles |
| Prohibited responsibilities | Trusting request ownership, global auditor reads, client-only authorization, mutating canonical resources, deciding validation outcomes |

The resolver now lives in `app/application/commands/access_scope.py` and uses
named identity/resource query ports plus declared cross-owner read models.
Inline SQL is absent from the application package. Repository and read-model
selection is checked statically and enforced by the PostgreSQL adapter at
runtime while preserving the SUB-60 contract and tests.

## Implemented Configuration Contract

`services/api-workflow/app/application/commands/configuration.py` owns the
constrained POC configuration schema and the explicit test, approve, activate,
supersede, retire, and rollback commands. PostgreSQL stores a mutable
per-contract draft separately from immutable numbered definitions, test
evidence, approvals, and lifecycle events. A small active-version projection is
the only mutable governance record and switches atomically during prospective
supersession. Invoice versions and validation runs reference the precise
historical snapshot by foreign key; neither UI state nor runtime AI can
activate or rewrite configuration.

The React administrator surface is a fixed projection over this contract:
category limits, five named rule settings, workflow labels, package labels,
governance rationale, permitted lifecycle actions, and immutable evidence
history. Later persona headers receive only the active version summary; no
generic expression editor or AI configuration path exists. Rollback prepares a
new tested candidate from retained history and still requires human approval
and supersession.

## Implemented Artifact Contract

`services/api-workflow/app/application/commands/artifacts.py` owns immutable artifact registration and authorized retrieval. PostgreSQL owns immutable metadata and predecessor relations; MinIO owns unique original/generated byte objects. Reads authorize against metadata before object access and verify both recorded size and SHA-256 before bytes leave the service.

## Implemented Provenance Contract

`services/api-workflow/app/application/commands/provenance.py` owns the typed append-only material event and field-lineage contracts plus authorized audit reads. Transaction-aware writers let canonical commands and their evidence commit atomically. PostgreSQL triggers reject historical mutation; projections are not used as audit evidence.

SUB-64 makes this contract executable rather than nominal. Material event
envelopes require canonical actor/role/organization context, resource scope,
contract, schema version, immutable version references, and an event hash.
`provenance_relations` validates the shared relation ontology and records all
eight POC relation types. `invoice_snapshots.py` captures immutable validation,
attestation, package, and submission inputs through the Invoices repository;
downstream records retain exact snapshot foreign keys. The auditor read model
traverses only canonically visible invoice, snapshot, submission, decision, and
relation records.

## Implemented Ingestion Job Contract

`services/api-workflow/app/application/commands/ingestion.py` validates configured upload families, registers immutable artifacts, and creates idempotent PostgreSQL jobs. The worker exclusively claims queued rows with locking and owns running/completed/failed transitions. Browser clients only upload and poll; they cannot inject results or set job state.

## Implemented Ledger Import Contract

`services/api-workflow/app/application/commands/ledger_import.py` deterministically normalizes the configured CSV/XLSX schema into decimal expense rows. Each row retains immutable artifact, sheet, physical row/cell coordinates, and importer/schema/mapping versions. Reconciliation to the activated configuration control total and row persistence occur atomically; failed inputs leave no partial canonical rows.

## Implemented OCR Extraction Contract

`services/api-workflow/app/application/commands/extraction.py` owns the
extraction use case against the replaceable application port in
`app/application/extraction_provider.py`; the Docker-local Tesseract
implementation is isolated in `app/adapters/extraction/tesseract.py`. The
worker owns execution; MinIO retains the immutable raw response; PostgreSQL
retains proposed fields, confidence, routing, versions, events, and lineage.
Extraction can only produce `needs_review` or `failed` and has no dependency
on validation or workflow authority modules.

## Implemented Human Review Contract

`services/api-workflow/app/application/commands/extraction_review.py` owns explicit accept/correct commands and the reviewed-value boundary. Proposed values remain historical evidence; mutable current projections point to append-only review records and successor lineage. Only the NGO Preparer can act, and downstream deterministic code cannot read an unreviewed proposal as canonical input.

## Implemented Draft Assembly Contract

`services/api-workflow/app/application/commands/invoice_draft.py` owns stable invoice-draft construction from the exact ledger import and configuration snapshot. It maps categories, links ledger/evidence/extraction records, computes Decimal totals and configured availability, emits unresolved assembly findings, and appends invoice-version lineage. It cannot attest, submit, or approve.

## Implemented Validation Contract

`services/api-workflow/app/application/commands/validation.py` owns the five versioned deterministic rules, normalized inputs, stable input/output hashes, results, and findings. It consumes only immutable invoice/configuration snapshots and Decimal/date primitives. It has no OCR/extraction dependency and cannot perform workflow authority.

`services/api-workflow/app/application/commands/budget.py` is the shared exact-Decimal budget calculator used by both validation and role-specific snapshots. Snapshots resolve the configuration referenced by the invoice and never read a newer draft; Government visibility remains submission-gated.

`services/api-workflow/app/application/commands/finding_resolution.py` owns Preparer-only correction/explanation/dismissal commands and the open-blocker gate. It never rewrites prior rule results: corrections and resolution history append evidence, then a new deterministic run produces the current projection used by later attestation.

## Implemented Attestation Contract

`services/api-workflow/app/application/commands/attestation.py` owns NGO Approver-only attestation. Its preview presents the exact invoice version, material revision, configuration, findings, validation hash/freshness, and planned package contents. The append-only attestation binds actor, role, fixed text/version, validation run, material revision, artifact hashes, and invoice content into a SHA-256 fingerprint. Any material revision makes the previous attestation stale and requires fresh deterministic validation plus a new human attestation.

## Implemented Package Contract

`services/api-workflow/app/application/commands/package_generation.py` is the
workflow coordinator for NGO Approver-only generation after a current
attestation. The Packages capability owns package persistence and the
application-owned deterministic rendering port; the ReportLab implementation
lives in `app/adapters/packages`. The coordinator assembles the validation
summary, claim/source manifest, evidence bundle, and ZIP from those owned
contracts. Generated bytes are stored through the immutable artifact boundary,
while append-only package indexes retain every path and SHA-256. Package
generation cannot attest, submit workflow state, or perform government
decisions.

## Implemented Submission Contract

`services/api-workflow/app/application/commands/submission.py` owns the NGO Approver-only atomic handoff. It requires the current attestation and matching generated package, snapshots every package hash, creates the government queue item, publishes package artifacts one-way, transitions workflow state, and appends the submitted event in one transaction. Database triggers prevent mutation of submitted invoice-line content.

## Implemented Government Queue Contract

`services/api-workflow/app/application/commands/government_review.py` owns agency-scoped submitted-package read models. It exposes the exact package/evidence hashes, deterministic validation and findings, configuration reference, and provenance summary only to the Government Reviewer organization. It does not edit NGO evidence or make decisions; return/approval commands are a separate authority boundary.

## Implemented Decision And Revision Contracts

`services/api-workflow/app/application/commands/government_decision.py` owns provisioned-human Government Reviewer return/approval commands and their strict state machine. Decisions are append-only and version/package bound. A return creates a successor through `revision.py`; the NGO Preparer can edit only that draft successor. V2 then traverses the same deterministic validation, separate attestation, package, and submission boundaries before approval. The predecessor remains immutable.

`revision.py` clones every v1 lineage record into v2 with an explicit
predecessor edge before any correction. The correction command appends a new
same-field successor and never overwrites the cloned record. The deterministic
finding-resolution path resolves the expense-date predecessor by the exact
`expenseDate` field, preventing the former claimed-amount cross-field edge.

## SUB-66 Recovery Boundary Decision

SUB-66 introduces no new runtime layer, capability, table owner, integration,
or network service. Its certification record maps 37 historical Done issues to
the current six-layer/nine-capability architecture and proves all ten recovery
prerequisite merge SHAs are in `origin/master` with post-merge evidence.

The boundary decision is `Certified with exceptions` for development
continuation after immutable AI approval, merge, and clean verification. The
remaining Journey 11 work may not infer new authority from this decision:
SUB-26, SUB-50, SUB-53, and SUB-55 remain blocked, and the runtime must retain
canonical server authorization, capability-owned statements, immutable
snapshots, deterministic validation/package contracts, and human-only
attestation/submission/return/approval.

## SUB-49 Exact Government Decision Boundary

The existing Workflow owner retains return/approval orchestration and decision
tables. Exact affected-line validation consumes only expense keys through the
Invoices-owned `GOVERNMENT_DECISION_READ_INVOICE_LINES_009` application query
port. Workflow does not gain invoice persistence ownership, and the HTTP/UI
layers do not become authority sources.

All structured evidence is validated before the transaction writes a decision,
updates queue/invoice state, creates a successor, or appends provenance. The
event keeps the Government organization as actor organization and the NGO as
resource organization. This is an implementation refinement inside ADR 0002;
it adds no layer, service, table owner, or network boundary.

## SUB-46 Returned Revision And Resubmission Boundary

The revision command remains in the Invoices application capability. It uses
capability-owned repositories for successor state and a declared read-only
Invoices/Workflow model solely to bind the correction to the exact Government
decision line keys. The command cannot accept caller-supplied tenant scope,
mutate the Workflow decision, or expose a raw database connection.

The returned v2 line is editable only by the assigned NGO Preparer. Validation,
attestation, package generation, and resubmission remain separate deterministic
and human-authority commands; a distinct NGO Approver session is required.
Provenance appends the correction/decision link. No service split, shared table
ownership, cross-capability write, AI authority, or client-side authorization
exception is introduced.

## SUB-50 Audit Projection Boundary

Provenance owns audit reconstruction and reads only declared capability ports.
The new `/audit/timeline` route is GET-only and returns the generated
`AuditTimelineDto`; the Audit web feature owns transport/rendering and contains
no command callback. Canonical contract assignment and submitted state control
visibility. The projection enriches retained evidence with canonical actor
references and explicit claim-to-package trails but never writes or infers
authority from a client identifier.

Submission consults an Invoices-owned application query port to distinguish a
linked successor and emit `resubmitted`. Extraction review emits
`field_corrected` for a correction and `field_reviewed` for acceptance. These
are ontology-alignment refinements, not new ownership or cross-owner writes.

## SUB-26 Playwright Certification Boundary

The Journey 11 harness is an external browser client. It may drive only normal
web controls and public HTTP behavior; it cannot import application internals,
write persistence, switch roles, or call a test-only mutation surface. The
supported reset command is an environment precondition and completes before
the worker starts. Each persona receives a distinct server session and logs out
before the next login.

The isolated Compose override changes only published test ports and volume
identity. API, worker, web, PostgreSQL, and MinIO images and authority
boundaries remain the production-shaped POC runtime. Playwright retains media
and results but does not become a system of record; canonical assertions query
the user-visible server projections, including v1/v2 package hashes and the
read-only audit trail.

## SUB-53 Operator Boundary

The operator script composes existing PostgreSQL, MinIO, API, worker, and web
units; it does not enter the modular-monolith application layers or own runtime
state. Migrate, seed, reset, and fingerprint operations invoke the supported
API management boundary. Browser certification delegates to the external
SUB-26 harness.

Stopping the worker during reset is process coordination, not a business-state
shortcut. The script cannot switch roles, mutate submitted evidence directly,
invent provenance, call an external AI provider, or grant authority. Port
overrides affect only host publication and preserve the internal Compose
network contract.

## SUB-55 Terminal Certification Boundary

SUB-55 adds one shared authenticated identity presentation component and final
release evidence. The component consumes only the generated identity contract,
maps its closed actor-role vocabulary to an explanatory permission summary,
and invokes the existing logout callback. It owns no authorization policy,
command, state, persistence, event, configuration, or network request.

The browser certification remains an external client over normal web/API
surfaces. It asserts visible identity and bounded permissions for all five
personas, but server application policy and canonical assignments remain the
only authority source. The complete run uses isolated Compose state and cannot
import internals, mutate PostgreSQL/MinIO directly, switch roles, inject job
results, or perform a human decision without the corresponding persona.

## SUB-74 Configurable Document-Intake MVP Design Boundary

SUB-74 adds design evidence only. ADR 0003 and
`document-intake-mvp-policy.json` keep one modular monolith and assign
Configuration ownership of immutable profile definitions/lifecycle,
Extraction ownership of deterministic fingerprints and noncanonical cluster
projections, Artifacts ownership of bytes/hashes, Invoices ownership of exact
runtime snapshots, Provenance ownership of append-only references, and Web
ownership of projections only.

A cluster suggestion has no assignment or activation authority. Exact active
profile matches create draft fields; changed or unknown layouts retain evidence
and create no canonical expense. Local pinned OCR is permitted, while hosted
models, runtime LLM extraction, AI-assisted profile drafting, and system/AI
authority are prohibited. Runtime contracts and persistence remain gated on
SUB-75/SUB-76 and may not be inferred from this design PR.

## SUB-75 Configuration Evidence Boundary

Configuration continues to own the editable draft, immutable governed
versions, test evidence, approvals, lifecycle events, and prospective active
pointer. Migration 024 adds a draft revision and read-support indexes; it does
not introduce a second canonical projection or shared ownership.

The Configuration application command compares draft revision within its owner
transaction and revalidates exact test/approval hashes before activation. The
HTTP adapter transports generated DTOs and canonical sessions only. The Web
feature displays version evidence and server-derived projections without
owning a rule, lifecycle decision, tenant scope, or mutation authority.

One declared read model joins stable runtime references across Invoices,
Validation, Packages, Workflow, and Provenance. Its SQL and source owners are
machine registered, it is executable only through the read-model repository,
and its result is marked noncanonical. No command imports it, and no source
owner is written. This is the permitted audit/reporting collaboration seam,
not an arbitrary cross-capability SQL exception.

## SUB-76 Profile And Extraction Boundary Decision

Migration 025 assigns profile lifecycle/evaluation/activation records to
Configuration and fingerprint/cluster/match records to Extraction. The named
statement catalog, generated statement ids, table-owner catalog, module map,
and dependency policy reject arbitrary cross-capability access. The two
permitted collaborations are immutable query ports: active profile resolution
for Extraction and cluster-projection lookup for an authorized Configuration
draft-association command.

The local OCR adapter remains behind the existing replaceable extraction port.
Fingerprinting, field normalization, exact matching, safe routing, fixture
evaluation, and result hashing are pure deterministic domain functions. They
cannot validate reimbursement compliance, mutate an invoice, assign a profile,
or perform a human lifecycle action. Profile/version and runtime evidence is
append-only; only the prospective active pointer is replaceable.

The executable contract rejects an undeclared fingerprint specification,
underrepresented fixture suite, false cross-profile predecessor, or unresolved
configuration profile reference before mutation. The layout fingerprint uses
value-free line shapes and normalized non-empty-line positions, and the runtime
ledger comparison consumes the approved profile field mapping rather than
hard-coded canonical names.

## SUB-77 Administrator Workspace Boundary Decision

The complete Configuration Administrator workspace is a noncanonical Web
projection over the SUB-75/SUB-76 server seams. It adds no table, repository,
worker, event writer, lifecycle rule, OCR/model adapter, or authority owner.
Transport remains isolated in the configuration feature API module, while the
application shell clears and reloads every configuration/profile/cluster read
model when the authenticated contract context changes.

The workspace may explain current state, history, comparison, provenance,
evaluation metrics, prospective impact, and next action. It may collect exact
ids, draft revision, rationale, and explicit confirmation. It may not infer
tenant scope, manufacture evidence, assign a profile, activate a cluster,
validate an invoice, or perform a human-authority action. All commands are
re-resolved and authorized by their canonical server owner.

The wide authenticated shell and no-horizontal-overflow browser assertion are
presentation evidence only. They do not change the existing modular-monolith,
data-flow, or authority boundary.

## SUB-78 Terminal MVP Boundary Decision

The four non-administrator landing pages are explanatory projections over the
same canonical invoice and server authority used by Journey 11. They show
useful next action, bounded authority, unavailable actions, contract scope, and
exact current/historical version context; they do not hide an action as the
only enforcement mechanism. The Government Reviewer remains scoped to
submitted agency queue items, and the Auditor remains submitted-only and
mutation-free.

Exact active profile references are Configuration-owned. Exact invoice review
references are read through Invoices/Workflow seams. Exact package profile
references are reconstructed by Provenance from immutable validation input
manifests. The declared read-model catalog remains the only cross-owner query
surface, and no command consumes the role projection.

No new ADR is required because ADR 0003 decision 7 explicitly assigns role
landing pages to Web projections and decisions 4/5 already require exact
historical references and the modular-monolith ownership split.
