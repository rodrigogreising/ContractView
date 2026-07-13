# Service Boundaries

This document defines the service and package boundaries future implementation work must preserve. It complements the system map by making ownership and isolation rules explicit.

For the POC, "service" means a capability module inside the
[enforceable modular monolith](modular-monolith.md), not a network deployment.
The [machine-readable policy](modular-monolith-policy.json) is authoritative for
layers, owners, and allowed dependencies.

## Boundary Principles

- Services own behavior and data together.
- Shared packages define contracts, not hidden service dependencies.
- Provenance, configuration, validation, and workflow are separate concerns even when initially implemented in one deployable.
- Product screens may differ by role, but all roles observe the same canonical invoice lifecycle.
- Each canonical record, table, repository, and migration has exactly one capability owner.
- Shared PostgreSQL is physical infrastructure; direct cross-capability SQL and shared mutable ORM models are forbidden.

## Layer Boundary Matrix

| Layer | May depend on | Owns ports/adapters |
| --- | --- | --- |
| Domain | Nothing | Domain contracts only |
| Application | Domain | Repository, capability, authorization, unit-of-work ports |
| Persistence | Application, Domain | Owner repository and transaction adapters |
| Integration | Application, Domain | Provider adapters and composition root |
| Worker | Application, Domain | Job transport only |
| HTTP | Application, Domain | Session/DTO transport only |

Dependencies point inward. HTTP and worker cannot import persistence adapters.
Application cannot import provider SDKs. Persistence/integration implement
application ports and contain no authority or validation decisions.

SUB-62 enforces this matrix through
`module-ownership-policy.json`, `scripts/check_module_boundaries.py`, and the
physical packages under `services/api-workflow/app/{domain,application,adapters,http,worker_runtime,integration}`.
The API and worker module names remain thin composition entrypoints; they do
not contain routes, polling behavior, SQL, or domain decisions.

## Capability-Owned Persistence

`app/application/ports/persistence.py` owns the repository and unit-of-work
interfaces. `app/adapters/persistence/statements.json` is the owner adapter's
SQL catalog. Every catalog entry declares its owner, consumer capability,
operation, read/write tables, source owners, and whether collaboration is an
owner repository, application query/command port, or declared read model.

The PostgreSQL adapter exposes identity, configuration, artifacts, extraction,
invoices, validation, packages, workflow, provenance, and platform
repositories plus a read-model repository. It rejects a statement when the
selected repository does not own it. Application, HTTP, worker, and domain
packages contain no SQL; migrations and runtime bootstrap remain explicit
integration exceptions and every referenced table is present in the physical
ownership map.

The statement validator also requires the calling application module to match
the catalog's `consumerCapability` and checks collaboration-kind semantics.
Argon2 password verification, OpenPyXL workbook parsing, ReportLab PDF
rendering, Tesseract OCR, and MinIO object access are concrete integration
adapters behind application-owned ports; application commands do not import
those provider packages.

## Service Responsibility Matrix

| Capability | Owning unit | Required evidence |
| --- | --- | --- |
| Organization and user roles | API/workflow service | Role assignment event, permission decision record for material actions |
| Contract and budget setup | Configuration registry | Configuration bundle version and activation approval |
| Configuration lifecycle | Configuration capability | Immutable test evidence, human approval, lifecycle event hash, predecessor/successor/rollback references, and prospective active projection |
| File upload intake | Ingestion service | Artifact hash, uploader, tenant, upload timestamp, scan result |
| Ledger import | Ingestion service plus extraction pipeline | Source row references, parser/importer version, draft field lineage |
| OCR and extraction | Extraction pipeline | Source location, confidence, model/parser version, correction history |
| Draft invoice assembly | API/workflow service | Invoice version, line-item relations, mapping version |
| Validation execution | Validation engine | Validation run with exact inputs, rule versions, reason codes |
| Issue workflow | API/workflow service | Issue events linked to invoice version and validation results |
| Package generation | Package generation service | Generated artifact hash, template version, package manifest |
| Submission | API/workflow service | Attestation event, submitted invoice version, package reference |
| Agency review | API/workflow service | Decision event, actor, role, reason, affected invoice version |
| Audit reconstruction | Provenance/event service | Event stream, lineage records, artifact references, validation runs |
| Dashboards and exports | Reporting layer | Read-model version, metric definition, source event/query reference |

The detailed one-owner allocation for identity, configuration, artifacts,
extraction, invoices, validation, packages, workflow, and provenance is in
`modular-monolith-policy.json`. Package generation owns package manifests and
indexes; the artifacts capability owns universal immutable object metadata and
bytes references. That distinction prevents duplicate ownership.

## MVP Capability Coverage

| MVP capability | Owning unit |
| --- | --- |
| Multi-organization accounts for one agency and multiple nonprofits | API/workflow service |
| Contract and budget configuration | Configuration registry |
| Manual file upload with immutable artifact storage | Ingestion service |
| CSV/XLSX ledger import | Ingestion service plus extraction pipeline |
| PDF/image document storage and basic OCR | Ingestion service plus extraction pipeline |
| Draft invoice assembly from structured ledger rows | API/workflow service |
| Configurable deterministic validation rules | Validation engine plus configuration registry |
| Versioned schemas, mappings, rule configuration, template configuration, and workflow state | Configuration registry plus API/workflow service |
| Append-only event log and field-level lineage for claimed amounts | Provenance/event service |
| Issue resolution workflow | API/workflow service |
| Nonprofit final approval | API/workflow service |
| Agency review queue | API/workflow service plus web app |
| PDF/CSV export package with validation summary | Package generation service |
| Complete audit and provenance trail | Provenance/event service |
| Basic dashboards for invoice status, cycle time, and open issues | Reporting layer |

## Boundary Details

### Web App

The web app renders role-specific workflows for nonprofit staff, agency reviewers, auditors, support users, and admins.

It may:

- Display canonical invoice state through role-specific views.
- Submit commands to the API/workflow service.
- Surface evidence, confidence, reason codes, and provenance summaries.

It must not:

- Implement compliance decisions only in client logic.
- Mutate invoice state without a workflow command.
- Create role-specific invoice copies.

### API/Workflow Service

The API/workflow service is the command boundary for material user actions.

It may:

- Own invoice lifecycle state.
- Enforce permissions for transitions and decisions.
- Coordinate ingestion, validation, package generation, and submission commands.
- Emit material workflow events.

It must not:

- Execute opaque AI compliance decisions.
- Modify submitted content without amendment, return, or resubmission semantics.
- Treat reporting projections as canonical state.

### Ingestion Service

The ingestion service handles file and data intake.

It may:

- Register uploaded artifacts.
- Coordinate malware scanning, deduplication, and checksum validation.
- Create import jobs for structured files.

It must not:

- Decide whether a claim is reimbursable.
- Approve, return, waive, or finalize invoices.

### Extraction Pipeline

The extraction pipeline turns artifacts into draft structured data with source references.

It may:

- Run OCR, parsers, importers, and AI-assisted extraction.
- Produce draft fields with source locations, confidence, and model/parser versions.
- Capture human corrections as lineage events.

It must not:

- Become the source of truth for compliance pass/fail.
- Overwrite corrected data destructively.

### Validation Engine

The validation engine executes deterministic checks over explicit inputs.

It may:

- Evaluate rules against invoice, artifact, budget, schema, mapping, workflow, and template versions.
- Produce pass/fail/warning/note results with reason codes.
- Record stable validation runs for reproducibility.

It must not:

- Query non-versioned mutable state during validation.
- Use AI output as an unreviewed blocking decision.
- Create approval, waiver, attestation, or finalization events.

### Package Generation Service

The package generation service creates agency-ready output from approved templates.

It may:

- Generate PDFs, CSVs, ZIP archives, manifests, and validation summaries.
- Record generated artifact hashes and template versions.

It must not:

- Fill missing compliance data with AI at generation time.
- Mutate generated submitted packages.

### Provenance/Event Service

The provenance/event service records material actions and lineage.

It may:

- Store append-only events.
- Link invoice fields to artifacts, source locations, validations, corrections, submissions, returns, approvals, and payment updates.
- Support audit reconstruction.

It must not:

- Be reduced to application logs.
- Allow event mutation without an explicit correction/amendment event.

### Configuration Registry

The configuration registry owns versioned reimbursement configuration.

It may:

- Store schemas, mappings, rules, workflows, views, templates, and configuration bundles.
- Enforce lifecycle states: draft, tested, approved, active, superseded, retired.
- Record activation approvals and test evidence.

It must not:

- Permit production use of unapproved AI-generated configuration.
- Hide customer-specific code behind configuration names.

### Reporting Layer

The reporting layer provides read models and analytics.

It may:

- Produce dashboards, exports, and operational metrics.
- Support portfolio, SLA, bottleneck, and error analytics.

It must not:

- Mutate canonical invoice state.
- Be the only source for certification evidence.

### Infrastructure Package

The infrastructure package defines how ContractView runtime units and managed resources are provisioned, configured, connected, and observed.

It may:

- Define deployment topology, environment configuration contracts, resource provisioning, secrets references, networking, observability wiring, backup policies, and recovery settings.
- Compose database, cache, object-storage, queue, and service resources from explicit versioned configuration.
- Emit deployment and infrastructure-change evidence through the delivery system.

It must not:

- Contain domain behavior, workflow decisions, validation rules, or service-owned schema definitions.
- Grant itself approval authority for production configuration or infrastructure changes.
- Make application services depend on a specific cloud provider through their domain interfaces.

### Persistence Package

The persistence package defines the database and cache system used by service-owned data boundaries.

It may:

- Define relational schemas, migrations, transaction helpers, storage adapter interfaces, cache namespaces, key formats, TTL policy contracts, and invalidation primitives.
- Provide deterministic migration ordering and compatibility checks.
- Expose explicit persistence contracts to services while keeping provider details behind adapters.

It must not:

- Own canonical domain data; each service remains the owner of the records in its schema and cache namespace.
- Permit cross-service table access, shared mutable models, cache-only audit evidence, or cache state as the source of truth.
- Hide destructive migrations, mutable submitted-package behavior, or provenance loss behind generic repository helpers.

The persistence package may depend on domain types needed to define storage contracts. Infrastructure may consume persistence deployment requirements. Persistence must not depend on infrastructure, apps, or service internals.

### Cross-Capability Persistence Rule

- Repository ports and unit-of-work interfaces live in application modules.
- Owner adapters may access only their declared table allowlist.
- Repositories never expose raw connections, ORM sessions, generic query
  builders, or table models to application code.
- Material cross-owner behavior uses a command/query port, immutable snapshot,
  versioned event, or declared read model.
- Read models may join owner data only for read-only reporting/audit use and
  cannot be used to mutate workflow state.
- Stable foreign ids do not grant write authority and cannot cascade mutation
  across capability owners.

## New Unit Checklist

Any new service or package must document:

- Owner role.
- Responsibilities.
- Data owned.
- Allowed dependencies.
- Events emitted.
- Configuration consumed.
- Deterministic behavior required.
- Human authority boundary.
- Prohibited responsibilities.

## Executable Shared Contract Boundary (SUB-61)

| Package | Owns | Allowed dependencies | Prohibited responsibilities |
| --- | --- | --- | --- |
| `domain-types` | Roles, resources, actions, lifecycle, artifact/field/entity/relation vocabulary, version references | Standard language/runtime only | Runtime state, persistence, workflow execution |
| `rule-contracts` | Rule definitions/results, severity/outcome, validation-run shape and determinism contract | `domain-types` | Rule execution, activation, human decisions |
| `event-contracts` | Material event names and versioned actor/aggregate/version envelope | `domain-types`, `configuration-contracts` | Event storage, workflow mutation |
| `configuration-contracts` | Workflow/view/template/bundle definitions and full lifecycle vocabulary | `domain-types`, `rule-contracts` | Activation, runtime invoice state, AI authority |

The dependency graph is acyclic and checked. Registries generate API/worker
Pydantic contracts and web TypeScript types; generated files are never edited
directly. Closed-vocabulary drift or stale consumers fail the shared-contract
validator. These packages emit no events, own no database tables, and grant no
human authority.

## Returned Revision Boundary (SUB-46)

- Owner role: Invoices owns successor state, cloned lines, version links, and
  revision corrections; Workflow owns the immutable Government decision;
  Provenance owns events, relations, and lineage.
- Allowed dependency: the Invoices application command reads the exact return
  decision through a declared, read-only cross-capability read model. It does
  not query Workflow tables through an Invoices repository or write them.
- Data and events: the editable successor references one immutable predecessor
  and decision. A correction appends lineage and an `invoice_line_corrected`
  event with invoice and decision version references.
- Deterministic behavior: only a line key contained in the bound return decision
  may change; invalid, unauthorized, stale, or unrelated-line requests roll
  back without material-revision, line, correction, lineage, or event mutation.
- Human authority: NGO Preparer alone corrects; NGO Approver separately
  revalidates, attests, packages, and submits; Government Reviewer alone makes
  the return/final approval decision. The web workspace grants no authority.
- Prohibited responsibilities: correction cannot mutate v1 evidence, select an
  arbitrary draft line, create validation findings, attest, submit, approve, or
  invoke AI.

## Configurable Document-Intake MVP Boundary (SUB-74)

| Owner | Owns | Collaborates through | Must not |
| --- | --- | --- | --- |
| Configuration | Profile definitions, immutable lifecycle, fixtures, evaluation evidence, confirmed associations, exact active bundle reference | Application commands, owner repository, immutable version query | Store artifact bytes, run OCR, auto-confirm clusters, mutate runtime invoices |
| Artifacts | Source bytes and hashes | Immutable artifact query port | Interpret layout or select profiles |
| Extraction | OCR execution, deterministic fingerprint, cluster projection, exact match result, draft fields | Versioned job and immutable extraction snapshot | Activate configuration, create canonical expense for unknown layouts, decide validation or human actions |
| Invoices | Editable draft plus immutable runtime snapshots with exact profile/configuration refs | Invoice commands and queries | Rewrite prior snapshots after activation |
| Provenance | Profile lifecycle events, source lineage, runtime references, audit reconstruction | Append-only evidence port and read-only projection | Become workflow state or a command-side cross-table escape hatch |
| Web | Administrator and role projections | Generated DTOs and normal authenticated HTTP commands | Own policy, lifecycle, profile matching, or authority |

The feature remains in the existing FastAPI deployment and worker. Direct
cross-capability SQL, shared mutable ORM models, implicit generic extraction,
and a new profile service are prohibited. The executable ownership catalogs
must be extended by SUB-75/SUB-76 before a table, repository, or statement is
introduced.

The owner-to-owner routing contract is closed: exact active matches return
`recognized_profile_draft`; changed or unknown layouts return
`needs_profile_review` with retained evidence and no canonical expense.

### SUB-76 Enforced Profile Boundary

Configuration repositories own profile versions, fixtures, evaluations,
approvals, lifecycle events, active assignments, and draft cluster
associations. Extraction repositories own fingerprints, cluster projections,
match results, OCR/extraction runs, and draft fields. The application unit of
work exposes separate owner repositories; no command receives a raw
connection or generic query surface.

Extraction may consume the exact active profile/configuration set through one
named immutable query port. Configuration may read a cluster projection only
to confirm an assigned administrator's draft association. Neither collaboration
permits a cross-owner write. Shared `extraction-contracts` describes the seam
without becoming a runtime owner.

Configuration also validates profile references inside its own transaction
before writing configuration test evidence. That validation replays immutable
Configuration-owned profile, fixture, evaluation, and approval records; it does
not read Extraction tables or transfer profile lifecycle authority. Extraction
executes the fixed fingerprint specification and profile-declared ledger field
mapping returned by the existing immutable query port.

## Explainable Configuration Read Boundary (SUB-75)

| Concern | Owner | Interface | Boundary control |
| --- | --- | --- | --- |
| Editable draft revision | Configuration | Owner repository and save/test commands | Compare-and-update under the Configuration transaction; stale revision returns no row and appends no evidence |
| Version detail, test evidence, approval, lifecycle | Configuration | Generated immutable DTOs | Exact version payload and append-only governance tables remain canonical |
| Human-readable diff | Configuration projection | Pure canonical-JSON comparison of two immutable versions | Sorted changes plus projection hash; `canonical=false`; no persistence table |
| Activation impact | Configuration projection | Active-version query plus derived runtime-reference counts | Prospective scope only; historical records are never selected for mutation |
| Runtime references | Configuration read model | Declared read-only join over Invoices, Validation, Packages, Workflow, and Provenance | Read-model repository only; source owners and SQL footprint are machine checked; no writes |
| Bounded web evidence | Web | Generated TypeScript DTOs and normal authenticated GET/command paths | Displays server results; owns neither lifecycle nor authorization |

Migration 024 adds only the Configuration-owned draft revision and read-support
indexes. It creates no cross-capability projection table. The named statement
catalog declares the multi-owner reference query as a `declared-read-model`;
the repository adapter rejects it through every owner repository and exposes
it only through `read_models`. Commands continue to use the Configuration
repository and cannot consume the read projection as mutation input.

Full version history/detail/diff/impact/reference reads and all lifecycle
commands resolve canonical contract assignment and require the Configuration
Administrator. NGO and Government roles retain the existing scoped active
summary; Auditor reconstruction remains the submitted, read-only Provenance
projection. This is an intentional least-privilege split, not role-specific
copies of configuration state.

## SUB-77 Administrator Web Projection Boundary

SUB-77 changes no capability owner or persistence collaboration. The Web
projection consumes the existing generated configuration DTOs and typed
profile/cluster read responses through `features/configuration/api.ts`.
`App.tsx` owns session- and contract-scoped orchestration;
`ConfigurationWorkspace` adapts the authenticated role workspace; and feature
components render evidence and emit exact typed commands.

Allowed browser responsibilities are navigation, form state, explicit impact
confirmation, accessible loading/error/empty states, and derived presentation
of the next action. Prohibited responsibilities are direct SQL, cross-owner
joins, lifecycle eligibility, fixture evaluation, profile matching, validation,
tenant scope, and human authority. Profile-reference staging remains an
editable-draft command and cluster confirmation remains a draft-association
command; neither is activation.

The local profile and cluster TypeScript types describe server read models and
do not create canonical domain vocabulary. Lifecycle states, exact version
references, evaluation evidence, and command validity continue to be owned by
the generated/shared contracts and server capabilities.

## SUB-78 Role And Certification Projection Boundary

SUB-78 adds no owner, table, deployable, network hop, or command collaboration.
The generated active-configuration and audit-package DTOs evolve additively
with exact profile/configuration references. Existing Invoice and Workflow
queries return the same references from their authorized configuration version.
These are read projections over persisted owner data; they are not command
inputs and cannot replace canonical authorization.

The shared role dashboard owns only explanatory presentation: next action,
authority, unavailable actions, selected contract, current prospective intake
context, and exact assigned-work context. Feature workspaces continue to own
their existing actions. The Auditor remains read-only and receives historical
submitted evidence rather than the active configuration endpoint. Forbidden
cross-owner writes, client-derived scope, client lifecycle decisions, and
stakeholder-specific invoice copies remain prohibited.
