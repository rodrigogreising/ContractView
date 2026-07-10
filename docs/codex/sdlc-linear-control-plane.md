# SDLC Linear Control Plane

Linear controls SDLC state, ownership, sequencing, blockers, and review handoffs. The repo remains the source of truth for durable evidence used in audit, release certification, and historical reconstruction.

## Operating Model

- Linear team: `Substrate`
- Linear project: `ContractView`
- Linear statuses: `Backlog`, `Todo`, `In Progress`, `In Review`, `Done`, `Duplicate`, `Canceled`
- Repo evidence: `solution_requirements.md`, `docs/adr/`, `docs/architecture/`, `docs/journeys/`, `docs/sdlc/`, and `docs/codex/`
- Skill location: `.agents/skills/`

Do not create custom Linear statuses for v1. Use labels, parent issues, child issues, links, and comments to represent SDLC gates.

## Lifecycle Stages

| Stage | Parent issue | Generation skill | Review skill | Primary evidence |
| --- | --- | --- | --- | --- |
| Product intake and discovery | SDLC 01 - Product intake and discovery | `cv-generate-product-intake` | `cv-review-product-intake` | Problem statement, stakeholders, scope, success metric |
| Requirements traceability | SDLC 02 - Requirements traceability | `cv-generate-requirements-traceability` | `cv-review-requirements-traceability` | Requirement-to-ADR, journey, boundary, and release trace |
| Architecture and ADR review | SDLC 03 - Architecture and ADR review | `cv-generate-adr-architecture` | `cv-review-adr-architecture` | ADR draft or amendment and architecture impact |
| Service/package boundary review | SDLC 04 - Service/package boundary review | `cv-generate-boundary-review` | `cv-review-boundary-review` | Owner, dependency, data, event, config, and authority checklist |
| Security, privacy, and data governance review | SDLC 05 - Security, privacy, and data governance review | `cv-generate-security-privacy` | `cv-review-security-privacy` | Threat model, data classification, mitigations, accepted risks |
| AI evaluation and configuration governance review | SDLC 06 - AI evaluation and configuration governance review | `cv-generate-ai-governance` | `cv-review-ai-governance` | AI use, prohibited authority, versions, eval plan, human review |
| Implementation and tests | SDLC 07 - Implementation and tests | `cv-generate-implementation-tests` | `cv-review-implementation-tests` | Implementation, tests, deterministic checks, affected docs |
| End-to-end journey certification | SDLC 08 - End-to-end journey certification | `cv-generate-journey-certification` | `cv-review-journey-certification` | Journey execution evidence and certification criteria |
| Release readiness and evidence signoff | SDLC 09 - Release readiness and evidence signoff | `cv-generate-release-readiness` | `cv-review-release-readiness` | Release certification record, exceptions, signoff |
| Production operation, incident response, and postmortems | SDLC 10 - Production operation, incident response, and postmortems | `cv-generate-operations-postmortem` | `cv-review-operations-postmortem` | Runbook, incident record, root cause, corrective actions |

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

## Issue State Rules

- `Backlog`: captured but not triaged.
- `Todo`: accepted and ready for SDLC work.
- `In Progress`: generation skill or implementation work is active.
- `In Review`: matching review skill is running or findings are being addressed.
- `Done`: review passed and required repo evidence is linked.
- `Canceled` or `Duplicate`: terminal exceptions.

No issue should reach `Done` without linked repo evidence and a review decision comment.

## Child Issue Template

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
- Follow-up issues:
```

## Handoff Comments

Codex should comment on the Linear issue at each transition:

- Generation started.
- Artifact generated or updated, with repo path.
- Review started.
- Review result and findings.
- Fixes applied.
- Ready for next SDLC gate or blocked.

## Release Blockers

Treat the release as blocked when any in-scope journey depends on:

- Runtime AI as the source of truth for compliance decisions.
- Mutable submitted packages.
- Stakeholder-specific copies of the same invoice.
- Audit logging implemented only as application logs.
- Unapproved production configuration.
- Human-authority actions performed by system or AI actors.
- Missing provenance for submitted claimed amounts.
