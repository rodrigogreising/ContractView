# ADR 0002: Role-Based POC Runtime

## Status

Accepted; amended by SUB-59 and implemented for shared contracts by SUB-61 on 2026-07-11

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

## Authentication And Authority

- Seed five synthetic persona accounts with securely hashed passwords.
- Authenticate through the normal login endpoint and issue server-side cookie sessions.
- Logout revokes the server session.
- Every command authorizes persona, organization, resource scope, invoice state, and target version server-side.
- UI visibility improves usability but never substitutes for API enforcement.
- No role editor or user provisioning surface is built.

## Configuration

- Administrator edits a constrained reimbursement configuration through the UI.
- Activation creates an immutable version covering categories, limits, rule parameters, workflow/package labels, and output settings.
- Draft invoices use the active version at creation/revalidation; submitted versions retain their referenced configuration.

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
