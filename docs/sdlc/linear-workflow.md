# Linear SDLC Workflow

This document defines the recommended Linear workflow model for ContractView's regulated SDLC. The goal is to make architecture decisions, governance gates, feature flags, canaries, certification evidence, and release readiness visible without turning every checklist item into a brittle issue status.

## Operating Principle

Use a hybrid model:

- Project states represent the lifecycle of the overall ContractView initiative.
- Issue states represent real queues, handoffs, or decision points with an owner.
- Labels, templates, linked docs, and checklists track controls that can apply in parallel.
- Long-form evidence remains in repo docs, ADRs, release certification records, test output, and linked Linear documents.

## Project States

Use these states for the ContractView project lifecycle:

| State | Meaning | Exit criteria |
| --- | --- | --- |
| Backlog | Project exists but is not committed. | Product owner decides discovery should begin. |
| Discovery | Problem, stakeholders, pilot scope, and success metrics are being defined. | Scope is clear enough to map to requirements and journeys. |
| Requirements Mapping | Requirements are being mapped to ADR pillars, journeys, service boundaries, and release criteria. | Major requirements have traceability coverage. |
| Architecture Review | Material system-shape decisions, ADRs, service boundaries, data flows, and ownership are under review. | Required ADRs and architecture docs are accepted or explicitly deferred. |
| Build | Implementation work is active. | In-scope work is code-complete enough for verification and evidence gathering. |
| Validation and Evidence | Tests, provenance evidence, journey certification, config approval, AI evaluation, and security/privacy review are being assembled. | Evidence is complete or exceptions are explicit. |
| Flagged Rollout | Feature flags, tenant or pilot targeting, kill-switch behavior, and rollback paths are active. | Rollout controls are verified and release owner approves limited exposure. |
| Canary | Limited production exposure is running with monitoring and explicit success/failure criteria. | Canary passes, fails, or is extended with an owner and reason. |
| Release Readiness | Final certification, exceptions, known risks, and signoff are being reviewed. | Release decision is Certified, Certified with exceptions, or Blocked. |
| Released | Certified, or certified with accepted exceptions. | No further release action required. |
| Paused | Intentionally stopped but not canceled. | Project resumes or is canceled. |
| Canceled | No longer planned. | Terminal state. |

## Issue Workflow States

Configure the Substrate team issue workflow as follows:

| State | Use when | Exit criteria |
| --- | --- | --- |
| Backlog | Work is captured but not triaged. | Triage owner accepts it for review. |
| Triage | Validity, priority, ownership, and duplication are being assessed. | Issue is canceled, deduplicated, sent to discovery, or accepted. |
| Discovery | Problem, users, scope, and acceptance criteria are being clarified. | Acceptance criteria and scope are clear. |
| Requirements Mapped | Traceability is being established. | Issue links to requirement, ADR pillar, affected journey, service/package boundary, and release criterion where applicable. |
| ADR / Architecture Review | The issue changes architecture, data ownership, service boundaries, AI authority, compliance boundaries, or rollout architecture. | Required ADR and architecture review are complete or explicitly not required. |
| Risk Review | Security, privacy, data governance, AI governance, or configuration governance review is needed. | Risks are mitigated, accepted, or converted into blocking follow-up work. |
| Ready for Build | Implementation-ready. | Engineer starts work. |
| In Progress | Implementation is active. | Work is ready for code review. |
| Code Review | Pull request or implementation review is active. | Review is approved or sent back to In Progress. |
| Verification | Automated tests, manual checks, journey evidence, config tests, provenance checks, or AI eval evidence are being completed. | Verification passes or required fixes are opened. |
| Release Certification | Release-facing evidence or signoff is required before Done. | Evidence is linked and release decision impact is clear. |
| Rollout Ready | Flag, targeting, monitoring, rollback, canary criteria, and owner are defined. | Limited rollout starts or the issue returns for missing controls. |
| Canary / Limited Rollout | Change is exposed to limited users, tenants, or traffic with active monitoring. | Canary passes, fails, or is extended with explicit owner and criteria. |
| Done | Completed, verified, and no further SDLC action is required. | Terminal successful state. |
| Duplicate | Issue duplicates another tracked item. | Terminal exception state. |
| Canceled | Work is intentionally abandoned. | Terminal exception state. |

`Blocked` should be a label, not a status, because a blocked issue can be blocked in any stage.

## Labels

Use labels for controls that may apply in parallel instead of turning each control into a state.

Gate labels:

- `gate:adr`
- `gate:architecture`
- `gate:security-privacy`
- `gate:ai-governance`
- `gate:config-governance`
- `gate:release-certification`

Evidence labels:

- `evidence:journey`
- `evidence:provenance`
- `evidence:deterministic-validation`
- `evidence:config-version`
- `evidence:runbook`

Rollout labels:

- `rollout:feature-flag`
- `rollout:kill-switch`
- `rollout:tenant-targeted`
- `rollout:canary`
- `rollout:rollback-plan`

Risk labels:

- `risk:human-authority`
- `risk:sensitive-data`
- `risk:auditability`
- `risk:ai-authority`
- `risk:configuration-drift`

## Required Issue Template Sections

Issues that enter the detailed SDLC workflow should include the relevant sections below. Not every issue needs every section, but missing sections should be intentional.

### Traceability

- Requirement:
- ADR pillar:
- Affected journey:
- Affected service/package boundary:
- Release certification criterion:

### Architecture

- Architecture impact:
- ADR required: Yes / No
- ADR link:
- Service or package ownership change:
- Data ownership change:

### Governance

- Security/privacy impact:
- AI governance impact:
- Configuration governance impact:
- Human authority impact:
- Accepted risks or exceptions:

### Feature Flag And Rollout

- Feature flag name:
- Default state:
- Targeting rule:
- Owner:
- Kill switch:
- Rollback path:

### Canary

- Canary scope:
- Start criteria:
- Success criteria:
- Failure threshold:
- Monitoring signals:
- End decision:

### Release Evidence

- Test results:
- Journey evidence:
- Provenance evidence:
- Configuration version evidence:
- Runbook link:
- Certification impact:

## Done Standard

An issue should only reach Done when:

- Implementation is complete or the issue was non-implementation work.
- Required reviews are complete.
- Required evidence is linked.
- Feature flag and rollout controls are documented when applicable.
- Canary result is recorded when applicable.
- Release certification impact is clear.
- Any exceptions have an owner, risk, compensating control, and target resolution.

This workflow intentionally keeps detailed SDLC controls auditable in Linear while preserving the repo as the authoritative source for architecture, ADRs, journey specs, release certification records, and long-form evidence.
