# ADR 0002: Role-Based POC Runtime

## Status

Accepted; amended by SUB-59, implemented for shared contracts by SUB-61,
physically enforced for module/persistence boundaries by SUB-62, and amended
for reproducible validation/package execution by SUB-68 and web feature
ownership by SUB-65

## Date

2026-07-11

## Context

ContractView needs a technically real, interview-ready POC rather than a production pilot. It must demonstrate configuration, ingestion, one real AI-assisted extraction path, deterministic validation, role-separated NGO and government decisions, immutable package revisions, and audit reconstruction through a recorded Playwright journey.

## Decision

Build the POC as a modular monolith with separately runnable web, API, worker, PostgreSQL, and MinIO processes under Docker Compose.

- React/TypeScript owns role-specific presentation and Playwright-visible behavior.
- FastAPI owns sessions, authorization, workflow commands, canonical invoice state, configuration lifecycle, validation coordination, package commands, and audit queries.
- A Python worker owns asynchronous import and OCR/LLM extraction jobs.
- PostgreSQL owns canonical transactional state, sessions, job records, append-only domain events, and field lineage.
- MinIO owns immutable original and generated artifact bytes; PostgreSQL stores hashes and references.
- Shared packages define domain, configuration, event, and rule contracts without becoming hidden services.

The POC keeps logical boundaries from ADR 0001 while avoiding deployable microservices. Modules may later split behind the same contracts.

## SUB-59 Amendment: Enforceable Modular Monolith

The modular monolith is normative, not an informal folder convention. The
controlling readable design is
`docs/architecture/modular-monolith.md`; the machine-readable contract is
`docs/architecture/modular-monolith-policy.json`.

The API and worker implement six inward-facing layers:

1. Domain owns invariants and vocabulary and has no framework dependency.
2. Application owns commands, queries, repository/capability ports, policy
   orchestration, and unit-of-work interfaces.
3. Persistence implements capability-owned repositories and migrations.
4. Integration implements MinIO, OCR/LLM, renderer, clock/id, and external
   adapters and owns the composition root.
5. Worker translates versioned jobs into idempotent application commands.
6. HTTP translates authenticated requests into application commands/queries.

The dependency direction is toward domain/application. Domain and application
do not import adapters. HTTP and worker do not contain domain decisions or SQL.

Canonical data is owned exactly once by identity, configuration, artifacts,
extraction, invoices, validation, packages, workflow, or provenance. A shared
PostgreSQL deployment does not create shared ownership. Direct
cross-capability SQL, command-path joins, table writes, shared mutable ORM
models, and repository connection escape hatches are prohibited. Collaboration
uses application command/query ports, immutable snapshots, versioned events,
or declared read models.

The ontology becomes executable shared contracts for artifacts, typed fields,
entities, relations, rules, workflows, views, templates, events, validation
runs, configuration bundles, invoice snapshots, package manifests, closed
vocabulary, and exact version references. Configuration definitions and
runtime evidence are distinct: activation is prospective and immutable runtime
records reference exact versions.

This amendment adds no network services or distributed transactions. REC-05
implements shared contracts; REC-07 implements repository boundaries,
forbidden-import rules, table ownership, and CI fitness tests.

## SUB-61 Implementation Note: Versioned Shared Contracts

The four shared contract packages now contain semantic-versioned executable
registries. A deterministic generator produces framework-light Pydantic
contracts for the API/worker and TypeScript contracts for the web consumer.
Authorization roles, resource kinds, actions, and material event names consume
the generated vocabulary. Identity, active-configuration, and validation DTOs
are generated for React use rather than re-declared in the application file.

The compatibility rule is additive within a minor version: optional fields may
be added, while removals, required-field changes, semantic reinterpretation,
and closed-vocabulary changes require a major version and coordinated consumer
migration. Generated-output, dependency-cycle, compatibility, runtime
validation, and TypeScript consumer tests enforce the decision. This does not
activate configuration or expand AI/human authority.

## SUB-62 Implementation Note: Enforced Module And Persistence Ownership

The logical layers now have executable package boundaries. Generated contracts
and authorization live in `app/domain`; application commands live in
`app/application/commands`; repository, object-store, runtime-health, and
extraction, password verification, spreadsheet parsing, and PDF-rendering
interfaces are application-owned ports; PostgreSQL, MinIO, Tesseract, Argon2,
OpenPyXL, and ReportLab implementations live under `app/adapters`; FastAPI routes live under
`app/http`; worker polling and health live under `app/worker_runtime`; and
`app/integration` is the only composition root. `app.main`, `app.worker`, and
`app.worker_health` are thin deployable compatibility entrypoints, so the POC
still has one API and one worker.

All application SQL is identified by an application-owned `Statement` value
and stored in the PostgreSQL persistence adapter catalog. The catalog assigns
each statement and each of the 39 physical tables to exactly one capability.
The unit-of-work exposes only capability repositories plus explicitly declared
read models; repositories reject inline SQL, foreign-owner statements, and
read-model misuse at runtime. Cross-capability writes are separate owner
commands coordinated by the application transaction. Boundary fitness tests
reject forbidden layer imports, inline SQL outside persistence/integration,
unowned migration tables, repository/table mismatches, and multi-owner write
statements.

## Authentication And Authority

- Seed five synthetic persona accounts with securely hashed passwords.
- Authenticate through the normal login endpoint and issue server-side cookie sessions.
- Logout revokes the server session.
- Every command authorizes persona, organization, resource scope, invoice state, and target version server-side.
- UI visibility improves usability but never substitutes for API enforcement.
- No role editor or user provisioning surface is built.

## Configuration

- Administrator edits a constrained reimbursement configuration through the UI.
- Testing creates an immutable numbered version and deterministic evidence
  covering categories, limits, rule parameters, workflow/package labels, and
  output settings.
- A canonically assigned human Configuration Administrator records approval
  before initial activation or supersession. Direct draft-to-active transitions
  are prohibited.
- The lifecycle is `draft -> tested -> approved -> active -> superseded ->
  retired`. Rollback creates a new tested candidate from a retained predecessor;
  it does not reactivate history or bypass approval.
- Draft invoices use the active version at creation/revalidation; submitted versions retain their referenced configuration.

### SUB-63 Implementation Note: Governed Configuration Lifecycle

Configuration definitions, immutable test evidence, human approvals, lifecycle
events, and the mutable current-active projection have distinct persistence
contracts. Lifecycle events record actor, role, organization, rationale,
timestamp, evidence and approval references, predecessor/successor/rollback
references, and a deterministic event hash. Definitions and evidence are
append-only; only the active projection changes atomically during prospective
activation or supersession.

The API exposes explicit test, approve, activate, supersede, retire, rollback,
and history commands. The bounded React administrator workspace consumes those
commands and displays retained evidence; it cannot activate an editable draft.
AI/system actors receive no configuration authority. Existing invoice,
validation, package, and submission records keep exact historical configuration
foreign keys when the active projection changes.

### SUB-64 Implementation Note: Versioned Provenance And Invoice Snapshots

Material domain events use a versioned envelope that records the canonical
actor, actor role and organization, resource organization, contract, aggregate,
reason code when applicable, immutable version references, and a deterministic
SHA-256 hash. PostgreSQL rejects incomplete material envelopes and preserves
events, field lineage, typed relations, validation runs/results, and invoice
snapshots as append-only evidence.

Editable invoice state is not audit evidence. Validation, attestation, package,
and submission commands capture capability-owned immutable invoice snapshots
containing the exact invoice version, material revision, configuration,
line-item values, source artifact hashes, mapping versions, and lifecycle
state. Typed `supports`, `derived_from`, `maps_to`, `validated_by`,
`submitted_as`, `returned_as`, `amends`, and `approved_as` relations connect
those snapshots and authority decisions. A government return clones lineage
into a successor invoice; corrections append same-field successors while the
predecessor version and its snapshots remain unchanged.

### SUB-67 Implementation Note: Hermetic Certification

Every pull request and `master` push runs one pinned GitHub Actions job. Python,
Node, official Actions, and all container images are fixed to exact versions or
content digests. Static certification covers formatting, fatal lint, Python
types, shared-contract compatibility, persistence and module ownership,
architecture/SDLC policy, repository tests, frontend tests, and the production
web build.

Runtime certification creates a unique Compose project twice. Each pass starts
with new PostgreSQL and MinIO volumes, runs numbered migrations and the
synthetic reset, executes the complete API suite, verifies API/web/worker
health, and destroys all state. A stable fingerprint of seeded semantic data
must match across the independent passes. CI retains schema-valid JSON evidence,
command logs, service state, exact base/head SHAs, test counts, environment
versions, and SHA-256 artifact hashes. This certifies a PR candidate; Journey 11
and its Playwright artifacts remain the terminal POC release gate.

### SUB-68 Amendment: Reproducible Validation And Packages

Validation and package generation execute against immutable, content-addressed
inputs rather than mutable invoice projections. A validation input manifest
binds the exact invoice snapshot and source artifact hashes to schema, mapping,
rule, workflow, view/template, parser/model, extraction-contract, and active
configuration versions. The manifest hash is the validation input identity;
the validation run retains both identifiers and executes validated shared
`RuleDefinition` contracts.

Package generation captures its own package-stage invoice snapshot and a
versioned `Template` contract. A package build input fixes the template hash,
renderer version, canonical claim-column order, validation run/input manifest,
configuration, and source artifact hashes. The retained reproduction manifest
hashes that input plus every generated file and the final deterministic ZIP.
Reproduction re-executes from retained manifests and fails on any missing,
changed, or unverifiable dependency.

PostgreSQL owns append-only runtime manifests; MinIO owns immutable generated
bytes. Identical retained inputs must reproduce validation results and package
bytes exactly. Changed invoice/configuration/template/extraction inputs create
new traceable records and hashes. AI remains limited to draft extraction: its
provider/model/prompt/parser/schema identifiers are manifest inputs, never rule
outcomes or human-authority decisions.

### SUB-65 Implementation Note: Feature-Owned Web Application

The React deployment remains one application, but transport, session,
configuration, ingestion, invoices, validation, approval, government review,
revision, audit, and role workspaces have explicit modules. The application
shell coordinates typed feature APIs and presentation state; it no longer owns
HTTP response parsing, seeded credentials, fixed contract selection, or feature
rendering implementations.

Authenticated contract context is returned by a canonical server query over
contract ownership and explicit assignments. The client selects only from
those returned contexts; a caller-provided contract identifier never grants
authority. The shared `ContractContextDto` is generated for Python and
TypeScript. Demo credentials compile only when the explicit demo/test build
flag is enabled and are absent from the default production bundle. Client role
routing remains presentational; every command still authorizes the server
session, assignment, resource, and lifecycle state.

### SUB-46 Implementation Note: Returned Revision And Resubmission

No new ADR is required. SUB-46 makes the existing immutable revision decision
executable within the Invoices capability. A Government return atomically
creates one editable successor linked to the exact immutable predecessor and
decision. The correction command resolves canonical invoice scope and uses a
declared read model to prove that the requested expense key is one of the exact
lines named by that decision; an arbitrary line on the draft cannot be edited.

The Preparer correction appends a normalized correction record, same-field
lineage successor, material-revision increment, and versioned event referencing
the decision. A separate NGO Approver must then run deterministic validation,
attest, generate a new package, and resubmit. V1 package bytes/hashes,
validation findings, decision feedback, events, and snapshots are compared
before and after the complete v2 path. This implements ADR 0001 provenance,
determinism, and human-authority pillars without changing deployment shape or
capability ownership.

## AI Boundary

- One replaceable OCR/LLM adapter extracts draft fields from one supported synthetic receipt/vendor-invoice format.
- Each output records provider/model, prompt/parser version, source location, and confidence.
- Low-confidence or intentionally incorrect fixture output requires NGO human review.
- AI never creates deterministic findings, attestations, submissions, returns, approvals, or finalization.

## Deterministic And Immutable Behavior

- Service-period, required-evidence, budget, reconciliation, and duplicate rules execute deterministically against explicit versions.
- Package generation produces real PDF/JSON/ZIP artifacts and hashes.
- Submission locks the invoice/package version.
- Government return creates a linked draft revision; resubmission creates a new package hash without changing version 1.

## Consequences

### Positive

- The demo exercises real technology and authority boundaries without production-scale complexity.
- Docker Compose and synthetic fixtures make the result reproducible.
- Logical modules preserve an extraction path toward production architecture.

### Negative

- Single-database modules are less isolated than separate production services.
- Seeded authentication does not prove enterprise identity lifecycle.
- One document class does not prove broad extraction generality.

## Deferred

Multi-tenant production operations, identity administration, MFA/SSO, customer data, external procurement integration, payment, notifications, support access, retention automation, production SLOs, broad extraction, and hosted deployment.

### SUB-50 Implementation Note: Typed Read-Only Audit Projection

No new ADR is required. Provenance assembles a GET-only `AuditTimelineDto` from
submitted material events, typed relations, field lineage, immutable invoice
snapshots, and package reproduction/build manifests. `event-contracts` owns the
additive DTOs and generates both API and web consumers.

The projection resolves canonical actors and constructs an explicit claimed-
amount traversal from source artifact/location through validation and invoice
snapshot to each immutable package. Extraction corrections and second-version
submissions use the closed `field_corrected` and `resubmitted` event values.
This makes the executable ontology observable without adding a write path,
database owner, deployable, or AI/human authority.

### SUB-26 Implementation Note: Canonical Browser Harness

Journey 11 is now one Playwright scenario executed against the public web and
HTTP surfaces in an isolated Compose project. The harness uses the supported
deterministic reset command before starting the real worker, normal
server-issued login/logout for all five personas, and visible UI interactions
for every material lifecycle transition. It contains no test endpoint, direct
database edit, role-switch shortcut, or client-side authority substitution.

Headless CI and paced headed demo modes share the scenario and retain JSON,
video, trace, screenshots, runtime logs, and Compose state. The scenario binds
the captured v1 and v2 archive hashes back to the final audit trails, proving
immutable predecessor evidence and a distinct successor package. This is a
certification adapter around ADR 0002's existing boundaries, not a new runtime
layer, capability owner, or distributed deployment.

### SUB-53 Implementation Note: POC Operator Contract

No new ADR is required. `scripts/poc.sh`, Make aliases, npm aliases, and the POC
runbook form an operations adapter over the existing Compose topology and
supported management commands. They add no deployable, data owner, authority,
or provider integration.

The adapter enforces toolchain preconditions, waits for service health, stops
the worker around deterministic schema/object reset, prints the canonical reset
fingerprint, and delegates both browser modes to the SUB-26 harness. Parameterized
host ports support isolated concurrent projects without altering service
networking or application contracts.
