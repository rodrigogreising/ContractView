# Enforceable Modular Monolith

Status: Accepted design for the ContractView POC

Controlling decision: ADR 0002 amendment under SUB-59

Machine-readable policy: `docs/architecture/modular-monolith-policy.json`

## Deployment Boundary

ContractView is one modular monolith, not a set of network services. The POC
contains these deployable processes:

- React web application;
- FastAPI API process;
- Python worker process;
- PostgreSQL;
- MinIO.

The API and worker share versioned contracts and capability modules. Process
separation does not change domain ownership: the worker is an asynchronous
entry point into application commands, not a second implementation of business
logic. PostgreSQL is physically shared while tables, repositories, migrations,
and transactions remain capability-owned.

## Six Layers

The dependency direction is inward. A layer may depend only on the layers
listed below.

| Layer | Owns | Allowed dependencies | Prohibited responsibilities |
| --- | --- | --- | --- |
| Domain | Entities, value objects, lifecycle states, reason codes, domain invariants, and version-reference vocabulary | None | FastAPI, SQL, object storage, queues, OCR clients, environment variables |
| Application | Commands, queries, authorization orchestration, repository ports, capability ports, transaction/unit-of-work interfaces | Domain | SQL statements, HTTP/cookie details, provider SDKs, worker polling |
| Persistence | Capability repository adapters, migrations, transaction adapters, object metadata adapters | Application, Domain | Cross-capability table writes, business decisions, shared mutable ORM models |
| Integration | MinIO, OCR/LLM, hashing/rendering, clock/id, and future external-system adapters plus the composition root | Application, Domain | Workflow authority, validation truth, direct HTTP response construction |
| Worker | Queue polling, job leases, retries, and translation of jobs into application commands | Application, Domain | Domain decisions, direct SQL, direct object-store mutation outside ports |
| HTTP | Session/cookie transport, request/response DTO mapping, route registration, and application command/query invocation | Application, Domain | Authorization as UI visibility, direct SQL, cross-capability orchestration |

The integration layer owns composition because adapters point inward to
application ports. Domain and application code never import an adapter. HTTP
and worker entry points receive already-composed application handlers.

## Capability Ownership

Each canonical record has exactly one owning capability. Other capabilities
refer to stable identifiers, call application ports, consume immutable
snapshots, or read explicit projections.

| Capability | Owns canonical data and behavior | Exposes | Must not own |
| --- | --- | --- | --- |
| Identity and access | Organizations, users, sessions, organization/contract assignments, auditor grants, access-scope policies | Session queries and authorization decisions | Invoice lifecycle, customer-specific role code |
| Configuration | Contracts, budget versions, configuration definitions, lifecycle evidence, immutable bundle versions, activation/supersession/rollback records | Active/versioned contract, budget, and bundle queries plus lifecycle commands | Runtime invoice state or direct validation results |
| Artifacts | Artifact identity, immutable object reference, hash, media metadata, predecessor relation, integrity verification | Artifact registration/read ports | Extraction proposals, package manifests, approval state |
| Extraction | Jobs, attempts, parser/model executions, draft proposals, confidence, and human review/correction history | Reviewed field snapshots and extraction events | Deterministic findings or workflow decisions |
| Invoices | Editable draft aggregates, line items, material revisions, immutable invoice snapshots, revision graph | Draft commands and immutable snapshot queries | Attestations, government decisions, configuration definitions |
| Validation | Input manifests, validation runs, rule results, findings, reason codes, and resolution evidence | Deterministic validation commands and immutable results | OCR execution, attestations, submissions, approvals |
| Packages | Package reproduction manifest, package index, generated-file hashes, template execution result | Deterministic generation and package snapshot queries | Invoice mutation, attestation, submission state |
| Workflow | Invoice lifecycle state, attestations, submissions, queue entries, returns, approvals, and authority decision records | Permissioned workflow commands and role projections | Package bytes, validation truth, configuration mutation |
| Provenance | Versioned events, typed relations, lineage edges, actor/resource references, reconstruction queries | Append-only evidence writers and read-only reconstruction | Mutable operational projection as audit truth |

Reporting and role workspaces are projections, not canonical capabilities.
They may read published query ports or projection tables and may never mutate
the owners above.

## Application Collaboration

Cross-capability collaboration uses one of four explicit mechanisms:

1. A command port when one capability requests behavior from another.
2. A query port returning a versioned immutable snapshot.
3. A versioned domain event for asynchronous consequences.
4. A read-only projection for reporting or audit navigation.

An application command handler owns the use case and transaction boundary. It
may coordinate multiple repository ports through an application-defined unit
of work. Repositories do not expose database connections, ORM sessions, table
objects, or generic query escape hatches.

Material commands append provenance through the same unit of work when the
event and canonical mutation share a local transaction. Future service
extraction replaces that local coordination with an outbox and idempotent
consumer without changing the application contract.

## Capability-Owned Persistence

The shared database is a physical deployment optimization, not shared data
ownership.

- Every table and migration has one capability owner.
- Only that capability's persistence adapter may insert, update, or delete its
  rows.
- A repository can access only its owner's table allowlist.
- Application, HTTP, worker, domain, and integration code contain no SQL.
- Cross-capability command-path joins and writes are forbidden.
- Cross-capability reads use query ports, immutable snapshots, or dedicated
  read-model adapters with declared source owners.
- Stable foreign identifiers may be stored, but they do not grant write
  authority and must not use cascading mutation across owners.
- Audit reconstruction may join owner data in a read-only projection; that
  projection cannot become workflow truth.
- Generic helpers may implement connection, transaction, and migration
  mechanics, but cannot expose arbitrary SQL to capabilities.

REC-07 implements repository boundaries, table allowlists, forbidden imports,
and ownership tests against this policy.

## Executable Ontology

The ontology is executable shared contract code, not documentation-only nouns
or arbitrary dictionaries. `packages/domain-types`, `rule-contracts`,
`event-contracts`, and `configuration-contracts` define validated,
versioned contracts for:

- `Artifact`, `Schema`, `Field`, `Entity`, `Relation`, `Rule`, `Workflow`,
  `View`, `Template`, and `Event`;
- `ValidationRun`, `ConfigurationBundle`, `InvoiceSnapshot`, and
  `PackageManifest`;
- lifecycle states, actor roles, resource kinds, reason codes, event names,
  relation kinds, and immutable version references.

Unknown event, relation, lifecycle, actor, resource, or reason-code vocabulary
must fail validation at an owning application boundary. Compatibility tests
must prove API/worker/web DTOs use the same contract versions. SUB-61 provides
the registries, generator, Pydantic models, TypeScript types, and compatibility
fitness checks. REC-06 consumes the configuration lifecycle; REC-08 consumes
the versioned event/relation envelopes; REC-10 completes web DTO migration.

## Configuration And Runtime Split

Configuration describes how future runtime work executes. Runtime records
prove what actually happened.

| Configuration definitions | Runtime records |
| --- | --- |
| Schema and field definitions | Reviewed field values and source locations |
| Mapping definitions | Mapping application and lineage edges |
| Rule definitions and parameters | Validation input manifest, results, and findings |
| Workflow definitions | Invoice state and authority events |
| View definitions | Role projection responses |
| Template definitions | Generated package bytes, manifest, and hashes |
| Configuration bundle and lifecycle evidence | Invoice snapshot and exact configuration references |

Configuration becomes immutable when approved/activated. Runtime records never
embed a mutable "current configuration" object; they reference exact bundle,
schema, mapping, rule, workflow, view, template, parser/model, and contract
versions. Activation is prospective. Re-validation, re-generation, return, and
resubmission create new runtime records rather than rewriting history.

## HTTP And Worker Contracts

- HTTP authenticates the session, maps transport DTOs, invokes one application
  command/query, and maps typed errors. Server-side authorization remains in
  application policy and domain invariants.
- Worker claims a versioned job, invokes one idempotent application command,
  and records retry/failure outcome through owned ports.
- Neither entry point imports persistence adapters or another capability's
  implementation.
- Browser clients cannot submit job results, actor roles, validation outcomes,
  or workflow state as trusted facts.

## Future Extraction Seams

A capability can become a network service only when its application ports,
events, idempotency rules, data ownership, and failure semantics are already
explicit. Extraction does not permit a new service to share tables or reach
back into monolith internals. The POC adds no distributed transactions,
service mesh, or network deployment complexity.

## Current-State Gap And Transition

This document is the approved target, not a claim that the recovery-baseline
code already conforms. The measurements below are fixed to SUB-59 base SHA
`27a308678fb6ce7420e491bc63eaf9beb959bdd6`.

- `services/api-workflow/app` is currently a flat module directory rather than
  explicit domain/application/adapter/transport packages.
- Twenty-two application modules execute SQL directly, including workflow,
  validation, package, provenance, extraction, and HTTP-adjacent paths.
- `main.py` contains 262 lines of route and composition behavior rather than a
  thin HTTP adapter over application handlers.
- Shared domain, rule, event, and configuration packages were README
  placeholders at the SUB-59 measurement. SUB-61 replaces that specific gap
  with executable registries and generated API/web consumers.
- Several command modules join and mutate tables that this policy assigns to
  different capability owners.

SUB-59 does not conceal or partially refactor those gaps. REC-05 implements the
shared contracts. REC-07 moves SQL behind owner repositories, defines
application ports/unit-of-work boundaries, separates HTTP and worker adapters,
and adds import/table-ownership fitness tests. REC-12 reconciles prior
"implemented contract" claims against the resulting code.

## Fitness And Review Gates

SUB-59 certifies that the policy is decision-complete. REC-05 and REC-07 make
the contracts and physical boundaries executable. CI must ultimately fail on:

- a forbidden layer import;
- a direct cross-capability implementation import;
- SQL outside an owner persistence adapter;
- a repository accessing another capability's table;
- duplicate canonical data ownership;
- configuration/runtime contract overlap;
- an unknown or incompatible ontology/event contract;
- HTTP or worker code bypassing an application command/query.
