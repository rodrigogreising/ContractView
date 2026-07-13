# ContractView System Map

This document defines ContractView's target monorepo shape and recovery transition. It is a declarative ownership map; current conformance is measured separately and must not be inferred from module names.

The system must follow [ADR 0001](../adr/0001-core-architectural-pillars.md): end-to-end provenance, configurable reimbursement ontology, deterministic execution with AI-assisted configuration, and human authority over cross-organizational workflow. The POC runtime follows the [enforceable modular monolith](modular-monolith.md) and its [machine-readable policy](modular-monolith-policy.json).

## Architecture Intent

ContractView is organized as one modular monolith with clear capability owners and shared contract packages. The service-shaped folders are capability design evidence or future extraction seams; they are not permission to add network deployment or direct cross-capability implementation dependencies.

The first implementation target is an MVP pilot: one agency division, one contract portfolio, and multiple nonprofit providers.

## Intended Monorepo Units

### POC Runtime Layers

| Layer | Dependency direction | Runtime responsibility |
| --- | --- | --- |
| Domain | None | Invariants, typed ontology, lifecycle and reason-code vocabulary |
| Application | Domain | Commands, queries, ports, policy orchestration, unit of work |
| Persistence | Application, Domain | Owner repositories, migrations, transaction adapters |
| Integration | Application, Domain | MinIO/OCR/LLM/rendering adapters and composition root |
| Worker | Application, Domain | Job lease/retry transport into idempotent commands |
| HTTP | Application, Domain | Session transport and DTO mapping into commands/queries |

The FastAPI process contains the HTTP, application, domain, persistence, and
integration layers. The worker process reuses application/domain contracts and
receives composed adapters. Neither entry point owns business rules.

### Applications

| Unit | Responsibility | Primary users |
| --- | --- | --- |
| Web app | Role-specific nonprofit, agency, auditor, support, and admin screens over shared canonical state. | Nonprofit staff, agency reviewers, auditors, support, admins |
| Admin console | Configuration, onboarding, support access controls, rule/test management, and rollout controls. | Implementation specialists, customer admins, platform support |

The current POC web app implements transport, capability feature modules, and
five role workspaces inside one React deployment. Contract context is a
server-authorized generated DTO; demo credentials are an explicit demo/test
build input and are absent from the default production bundle.

### Services

| Unit | Responsibility | Must own | Must not own |
| --- | --- | --- | --- |
| API/workflow service | User-facing API, permissions, invoice lifecycle, issue workflow, state transitions. | Canonical invoice state, workflow commands, role checks. | Artifact storage internals, validation rule execution internals, reporting aggregates. |
| Ingestion service | Upload intake, malware scan orchestration, deduplication, artifact registration, import job creation. | Upload lifecycle, artifact intake metadata, ingestion jobs. | Invoice approval, compliance pass/fail decisions. |
| Extraction pipeline | OCR, structured import, source-location capture, field extraction drafts. | Parser/model execution records, extracted draft fields, confidence. | Submission-blocking validation decisions or human approvals. |
| Validation engine | Deterministic rule execution over invoice, evidence, budget, and configuration versions. | Validation runs, rule inputs/results, reason codes. | AI-only compliance decisions, workflow authority. |
| Package generation service | Deterministic generation of agency packages from approved templates and invoice versions. | Generated artifacts, package manifests, package reproduction metadata. | Source upload mutation, approval decisions. |
| Provenance/event service | Append-only material events, lineage, artifact/version references, reconstruction support. | Event log, field lineage, validation evidence, chain of custody. | Product workflow projections as source of truth. |
| Configuration registry | Versioned schemas, mappings, rules, workflows, views, templates, and activation lifecycle. | Configuration bundles and lifecycle state. | Runtime invoice state or customer-specific code paths. |
| Reporting layer | Operational projections, dashboards, exports, and analytical replicas. | Read models and metric definitions. | Mutable canonical invoice state. |
| Notification service | In-app/email notifications and future collaboration hooks. | Notification templates, delivery attempts, user notification state. | Workflow transitions without API/workflow authorization. |

### Shared Packages

| Package | Responsibility |
| --- | --- |
| Domain types | Shared definitions for ontology primitives, invoice lifecycle, issue statuses, and actor roles. |
| Rule contracts | Rule input/output interfaces, severity taxonomy, reason-code conventions, deterministic execution contract. |
| Event contracts | Event names, payload requirements, lineage references, and version reference shapes. |
| Configuration contracts | Schema, mapping, workflow, view, template, and configuration bundle definitions. |
| Extraction contracts | Deterministic profile-route, fingerprint, cluster, ledger-match, source-location, and intake-result definitions. |
| Infrastructure | Deployment topology, environment configuration contracts, resource provisioning definitions, and operational wiring for runtime units. |
| Persistence | Relational schema and migration definitions, cache key/TTL contracts, transaction boundaries, and storage adapter interfaces. |
| Test fixtures | Certified sample contracts, ledgers, artifacts, users, rule sets, and journey data. |

## Ownership Rules

- Canonical invoice state is owned by the API/workflow service.
- Immutable artifact bytes and artifact metadata are owned by ingestion plus object storage abstractions.
- Field lineage and material action history are owned by the provenance/event service.
- Runtime compliance decisions are owned by the deterministic validation engine.
- Configuration lifecycle and activation are owned by the configuration registry.
- Domain services retain ownership of their canonical data; the persistence package defines storage mechanics but does not become a shared data owner.
- The infrastructure package owns provisioning and deployment definitions, not application behavior or production approval authority.
- Role-specific screens are projections over shared canonical state, not separate stakeholder copies.
- Every canonical table, repository, migration, and transaction has one owner listed in `modular-monolith-policy.json`.
- Application command handlers coordinate capabilities through ports; no capability obtains another owner's database connection, ORM model, or table object.

## Dependency Rules

- Applications may depend on API contracts and shared domain types.
- Services may depend on shared packages, but must not import another service's internal implementation.
- Services may use persistence contracts and adapters only for data they own; they must not reach through the package into another service's tables or cache namespace.
- Infrastructure may compose deployable units and managed resources, but application packages and services must not depend on infrastructure implementation details.
- The validation engine reads explicit inputs and configuration versions; it must not query mutable UI state.
- The package generation service reads approved templates and invoice versions; it must not infer missing data with AI.
- Reporting reads projections or replicas; it must not mutate canonical workflow state.
- AI-assisted components may draft, classify, summarize, or suggest; they must not approve, waive, attest, finalize, or block submission.
- Direct SQL is limited to persistence adapters and their owner table allowlist.
- Cross-capability reads use query ports, immutable snapshots, events, or declared read models; cross-capability SQL writes and command-path joins are forbidden.

## Forbidden Coupling

- No service may silently mutate submitted packages.
- No runtime AI response may be the source of truth for compliance pass/fail decisions.
- No workflow state transition may bypass role checks in the API/workflow service.
- No stakeholder-specific invoice copy may diverge from canonical invoice state.
- No audit trail may exist only as application logs.
- No customer-specific workflow should require custom application code when it can be represented as versioned reimbursement configuration.

## Architecture Fitness Checks

Each material implementation change should answer:

- Which architectural pillar does this change support?
- Which service or package owns the new behavior?
- What canonical data does it create, read, update, or project?
- What events, lineage records, or configuration versions are required for reconstruction?
- Which user journey certification does it affect?
- What must remain deterministic?
- Which human actor retains authority?

## Document-Intake MVP Extension

ADR 0003 and the
[machine-readable MVP policy](document-intake-mvp-policy.json) extend the same
modular monolith; they do not authorize another deployable or a second domain
model.

| Capability | MVP ownership | Required seam |
| --- | --- | --- |
| Configuration | Immutable `DocumentProfileVersion`, profile fixtures/evaluation, lifecycle, confirmed assignment, and exact active bundle reference | Configuration commands and version queries |
| Artifacts | Immutable source bytes and hash | Artifact query port |
| Extraction | Versioned local OCR, fingerprint, noncanonical cluster projection, exact profile match, and draft fields | Job command plus immutable extraction snapshot |
| Invoices | Editable draft and immutable snapshots carrying exact profile/configuration references | Invoice command/query ports |
| Provenance | Profile lifecycle events, source locations, and reconstruction references | Append-only writer and read-only audit projection |
| Web | Administrator and role landing-page projections | Generated HTTP DTOs; no canonical state or authority |

Changed or unknown layouts produce `needs_profile_review` and no canonical
expense. Cluster projections may suggest families but cannot assign, approve,
or activate a profile. SUB-75 and SUB-76 must extend executable shared
contracts, table ownership, and named statements before runtime data is added.

SUB-76 implements this extension in the existing API and worker composition.
Configuration-to-Extraction collaboration is a named immutable query port for
the exact active configuration and profile versions. It grants no Configuration
write authority. Extraction returns a versioned intake result DTO and persists
only its owned OCR/fingerprint/cluster/match/draft records.
