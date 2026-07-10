# SDLC Linear Control Plane

Linear project statuses control feature and project state, sequencing, blockers, and review handoffs. The repo remains the source of truth for durable evidence used in audit, release certification, and historical reconstruction.

## Operating Model

- Linear team: `Substrate`
- Linear project: `ContractView`
- Linear project statuses: `Backlog`, `Discovery`, `Design Review`, `Build`, `Evidence Review`, `Rollout`, `Completed`, `Paused`, `Canceled`
- Repo evidence: `solution_requirements.md`, `docs/adr/`, `docs/architecture/`, `docs/journeys/`, `docs/sdlc/`, and `docs/codex/`
- Skill location: `.agents/skills/`

Use project statuses for the state of a feature or project. Use labels, milestones, linked docs, project status updates, and repo evidence links to represent SDLC gates.

## Lifecycle Stages

| Stage | Project status | Generation skill | Review skill | Primary evidence |
| --- | --- | --- | --- | --- |
| Product intake and discovery | `Discovery` | `cv-generate-product-intake` | `cv-review-product-intake` | Problem statement, stakeholders, scope, success metric |
| Requirements traceability | `Design Review` | `cv-generate-requirements-traceability` | `cv-review-requirements-traceability` | Requirement-to-ADR, journey, boundary, and release trace |
| Architecture and ADR review | `Design Review` | `cv-generate-adr-architecture` | `cv-review-adr-architecture` | ADR draft or amendment and architecture impact |
| Service/package boundary review | `Design Review` | `cv-generate-boundary-review` | `cv-review-boundary-review` | Owner, dependency, data, event, config, and authority checklist |
| Security, privacy, and data governance review | `Design Review` or `Evidence Review` | `cv-generate-security-privacy` | `cv-review-security-privacy` | Threat model, data classification, mitigations, accepted risks |
| AI evaluation and configuration governance review | `Design Review` or `Evidence Review` | `cv-generate-ai-governance` | `cv-review-ai-governance` | AI use, prohibited authority, versions, eval plan, human review |
| Implementation and tests | `Build` | `cv-generate-implementation-tests` | `cv-review-implementation-tests` | Implementation, tests, deterministic checks, affected docs |
| End-to-end journey certification | `Evidence Review` | `cv-generate-journey-certification` | `cv-review-journey-certification` | Journey execution evidence and certification criteria |
| Release readiness and evidence signoff | `Evidence Review` | `cv-generate-release-readiness` | `cv-review-release-readiness` | Release certification record, exceptions, signoff |
| Production rollout and post-release operations | `Rollout` | `cv-generate-operations-postmortem` | `cv-review-operations-postmortem` | Runbook, incident record, root cause, corrective actions |

## Label Taxonomy

Stage labels:

- `stage:product-intake`
- `stage:requirements-traceability`
- `stage:adr-architecture`
- `stage:boundary-review`
- `stage:security-privacy`
- `stage:ai-governance`
- `stage:implementation-tests`
- `stage:journey-certification`
- `stage:release-readiness`
- `stage:operations-postmortem`

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

Risk labels:

- `risk:human-authority`
- `risk:sensitive-data`
- `risk:auditability`
- `risk:ai-authority`
- `risk:configuration-drift`

Rollout labels:

- `rollout:feature-flag`
- `rollout:kill-switch`
- `rollout:tenant-targeted`
- `rollout:canary`
- `rollout:rollback-plan`

## Project Status Rules

- `Backlog`: project or feature exists but is not committed.
- `Discovery`: problem, stakeholders, pilot scope, and success metrics are being defined.
- `Design Review`: requirements, ADRs, architecture, boundaries, security/privacy, AI governance, and configuration governance are being worked through.
- `Build`: implementation and tests are active.
- `Evidence Review`: journey certification, provenance, deterministic validation, configuration evidence, AI evaluation, security review, release evidence, and signoff are being assembled.
- `Rollout`: feature flags, tenant targeting, canary, rollback, monitoring, and operational readiness are active.
- `Completed`: review passed, required repo evidence is linked, and no further project action is required.
- `Paused`: intentionally stopped but expected to resume.
- `Canceled`: no longer planned.

No project or feature should reach `Completed` without linked repo evidence and a review decision in a Linear project status update or linked repo artifact.

## Project Status Update Template

```markdown
## SDLC Control

- Stage:
- Generation skill:
- Review skill:
- Required repo artifact:
- Evidence links:
- Blocking gates:
- Release impact:

## Traceability

- Requirement:
- ADR pillar:
- Affected journey:
- Affected service/package boundary:
- Release certification criterion:

## Review Result

- Decision: Pending | Approved | Approved with required fixes | Blocked
- Reviewer:
- Findings:
- Follow-up work:
```

## Handoff Comments

Codex should use Linear project status updates at each transition:

- Generation started.
- Artifact generated or updated, with repo path.
- Review started.
- Review result and findings.
- Fixes applied.
- Ready for next project status or blocked.

## Release Blockers

Treat the release as blocked when any in-scope journey depends on:

- Runtime AI as the source of truth for compliance decisions.
- Mutable submitted packages.
- Stakeholder-specific copies of the same invoice.
- Audit logging implemented only as application logs.
- Unapproved production configuration.
- Human-authority actions performed by system or AI actors.
- Missing provenance for submitted claimed amounts.
