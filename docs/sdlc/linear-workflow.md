# Linear SDLC Workflow

This document defines the recommended Linear workflow model for ContractView's regulated SDLC. The goal is to make architecture decisions, governance gates, feature flags, canaries, certification evidence, and release readiness visible without turning every checklist item into a brittle project status.

## Operating Principle

Use a hybrid model:

- Project statuses represent the lifecycle state of each ContractView feature or project.
- Granular implementation work stays subordinate to the owning project and must not replace project status.
- Labels, templates, linked docs, and checklists track controls that can apply in parallel.
- Long-form evidence remains in repo docs, ADRs, release certification records, test output, and linked Linear documents.

## Project States

Use these states for the ContractView project lifecycle:

| State | Meaning | Exit criteria |
| --- | --- | --- |
| Backlog | Project exists but is not committed. | Product owner decides discovery should begin. |
| Discovery | Problem, stakeholders, pilot scope, and success metrics are being defined. | Scope is clear enough to map to requirements and journeys. |
| Design Review | Requirements, ADRs, architecture, boundaries, security/privacy, AI governance, and configuration governance are being worked through. | Required design and governance evidence is accepted or explicitly deferred. |
| Build | Implementation work is active. | In-scope work is code-complete enough for verification and evidence gathering. |
| Evidence Review | Tests, provenance evidence, journey certification, config approval, AI evaluation, security/privacy review, final certification, exceptions, known risks, and signoff are being assembled. | Evidence is complete, exceptions are explicit, and release decision impact is clear. |
| Rollout | Feature flags, tenant or pilot targeting, kill-switch behavior, canary, monitoring, and rollback paths are active. | Rollout passes, fails, or is extended with an owner and reason. |
| Completed | Certified, released, or otherwise completed with no further project action required. | Terminal successful state. |
| Paused | Intentionally stopped but not canceled. | Project resumes or is canceled. |
| Canceled | No longer planned. | Terminal state. |

If a feature needs a state, make it a Linear project and move the project through these statuses.

## Feature Status Rules

Use one Linear project per tracked feature, release, or major workstream. Move that project through the project statuses above as the source of truth for state.

Granular work items, when needed, are implementation details under the owning project and must not replace project status.

`Blocked` should be a label or status update condition, not a project status, because a feature can be blocked in any stage.

### Issue Delivery States

Leaf implementation issues use these states as source-integration gates:

| State | Required evidence |
| --- | --- |
| `Backlog` | Issue exists but is not dependency-ready. |
| `Todo` | All prerequisites are merged and post-merge verified. |
| `In Progress` | Issue branch exists from current `origin/master`; Linear records base SHA, scope, skills, and plan. |
| `In Review` | Draft PR is pushed; PR URL, base/head SHA, checks, and evidence manifest are recorded. |
| `Done` | PR is merged; merge SHA and clean post-merge verification are recorded. |

A dependent issue may not enter `In Progress` merely because a prerequisite is marked `Done`; every merged prerequisite and its post-merge evidence must also be verified.

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

## Required Project Status Update Sections

Projects or features that enter the detailed SDLC workflow should include the relevant sections below in project descriptions, project documents, or project status updates. Not every project needs every section, but missing sections should be intentional.

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

## Completion Standard

A project or feature should only reach `Completed` when:

- Implementation is complete or the project was non-implementation work.
- Required reviews are complete.
- Required evidence is linked.
- Feature flag and rollout controls are documented when applicable.
- Canary result is recorded when applicable.
- Release certification impact is clear.
- Any exceptions have an owner, risk, compensating control, and target resolution.
- Every implementation issue has an issue-scoped merged PR, reviewed base/head SHA, machine-readable evidence manifest, merge SHA, and clean post-merge verification.

This workflow intentionally keeps detailed SDLC controls auditable in Linear project state while preserving the repo as the authoritative source for architecture, ADRs, journey specs, release certification records, and long-form evidence.
