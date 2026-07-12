# POC Boundary Review

Status: SUB-62 implementation complete locally; immutable architecture,
boundary, and implementation review pending

SUB-59 design amendment: the runtime is governed by the
[enforceable modular monolith](modular-monolith.md) and
`modular-monolith-policy.json`. SUB-61 implements the shared ontology and
SUB-62 implements physical module/persistence enforcement. REC-12 must still
recertify the complete recovery baseline.

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

`services/api-workflow/app/application/commands/configuration.py` owns the constrained POC configuration schema and activation command. PostgreSQL stores a mutable per-contract draft and immutable numbered activation snapshots. Invoice versions and validation runs reference the precise snapshot by foreign key; neither UI state nor runtime AI can activate or rewrite configuration.

The React administrator surface is a fixed projection over this contract: category limits, five named rule settings, workflow labels, and package labels. Later persona headers receive only the active version summary; no generic expression editor or AI configuration path exists.

## Implemented Artifact Contract

`services/api-workflow/app/application/commands/artifacts.py` owns immutable artifact registration and authorized retrieval. PostgreSQL owns immutable metadata and predecessor relations; MinIO owns unique original/generated byte objects. Reads authorize against metadata before object access and verify both recorded size and SHA-256 before bytes leave the service.

## Implemented Provenance Contract

`services/api-workflow/app/application/commands/provenance.py` owns the typed append-only material event and field-lineage contracts plus authorized audit reads. Transaction-aware writers let canonical commands and their evidence commit atomically. PostgreSQL triggers reject historical mutation; projections are not used as audit evidence.

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
