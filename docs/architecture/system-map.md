# ContractView System Map

This document defines the intended monorepo shape for ContractView before implementation begins. It is a declarative architecture map, not a commitment to a specific framework, cloud provider, or deployment topology.

The system must follow [ADR 0001](../adr/0001-core-architectural-pillars.md): end-to-end provenance, configurable reimbursement ontology, deterministic execution with AI-assisted configuration, and human authority over cross-organizational workflow.

## Architecture Intent

ContractView should be organized as a modular monorepo with clear runtime units and shared packages. Each unit owns a small set of responsibilities and must expose explicit interfaces rather than reaching across boundaries.

The first implementation target is an MVP pilot: one agency division, one contract portfolio, and multiple nonprofit providers.

## Intended Monorepo Units

### Applications

| Unit | Responsibility | Primary users |
| --- | --- | --- |
| Web app | Role-specific nonprofit, agency, auditor, support, and admin screens over shared canonical state. | Nonprofit staff, agency reviewers, auditors, support, admins |
| Admin console | Configuration, onboarding, support access controls, rule/test management, and rollout controls. | Implementation specialists, customer admins, platform support |

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
| Test fixtures | Certified sample contracts, ledgers, artifacts, users, rule sets, and journey data. |

## Ownership Rules

- Canonical invoice state is owned by the API/workflow service.
- Immutable artifact bytes and artifact metadata are owned by ingestion plus object storage abstractions.
- Field lineage and material action history are owned by the provenance/event service.
- Runtime compliance decisions are owned by the deterministic validation engine.
- Configuration lifecycle and activation are owned by the configuration registry.
- Role-specific screens are projections over shared canonical state, not separate stakeholder copies.

## Dependency Rules

- Applications may depend on API contracts and shared domain types.
- Services may depend on shared packages, but must not import another service's internal implementation.
- The validation engine reads explicit inputs and configuration versions; it must not query mutable UI state.
- The package generation service reads approved templates and invoice versions; it must not infer missing data with AI.
- Reporting reads projections or replicas; it must not mutate canonical workflow state.
- AI-assisted components may draft, classify, summarize, or suggest; they must not approve, waive, attest, finalize, or block submission.

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
