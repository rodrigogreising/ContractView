# ContractView Codex Guidance

ContractView uses Linear project statuses as the SDLC control plane and this repository as the durable evidence store. Before material work, identify the controlling Linear project or feature, its project status, the SDLC stage, and the repo evidence that must be created or reviewed.

## Default Read Order

Before architecture, implementation, testing, release, or governance changes, read:

1. `solution_requirements.md`
2. `docs/adr/0001-core-architectural-pillars.md`
3. Relevant files in `docs/architecture/`
4. Relevant journey specs in `docs/journeys/`
5. Relevant SDLC gates in `docs/sdlc/`
6. `docs/codex/playbooks.md`
7. `docs/codex/sdlc-linear-control-plane.md`

## Linear Control Plane

- Use Linear project statuses for feature or project state.
- Use Linear project fields, labels, milestones, linked docs, and status updates for ownership, priority, target dates, blockers, rollout controls, and handoffs.
- Use the `Substrate` Linear team and `ContractView` Linear project unless the user explicitly chooses another target.
- Use these project statuses for state: `Backlog`, `Discovery`, `Design Review`, `Build`, `Evidence Review`, `Rollout`, `Completed`, `Paused`, and `Canceled`.
- Use Linear projects and project statuses to represent SDLC stage and feature state.
- Update the Linear project status and status update when generation starts, artifacts are updated, review starts, findings are returned, fixes are applied, and the feature is ready for the next state or blocked.

## Skill Invocation

- Use the matching `cv-generate-*` skill to create or update SDLC evidence.
- Use the matching `cv-review-*` skill before moving a Linear project or feature out of `Design Review`, `Evidence Review`, or into `Completed`.
- Review skills must return one decision: `Approved`, `Approved with required fixes`, or `Blocked`.
- If evidence is missing, name the missing artifact or decision directly rather than inventing it.

## Immutable Delivery Protocol

- Use exactly one Linear leaf issue per branch and pull request. A documented recovery exception requires explicit human approval.
- Start only when every blocking issue is `Done`, its PR is merged into `origin/master`, and its post-merge evidence is recorded.
- Require a clean tracked worktree and an up-to-date `master` before creating the issue branch.
- Record the branch, base SHA, applicable skills, declared file scope, dependencies, and expected evidence in Linear before implementation.
- Use issue states in this order: `Backlog` -> `Todo` -> `In Progress` -> `In Review` -> `Done`.
- Move to `In Review` only after pushing a complete draft PR and recording its URL and head SHA.
- Run review skills against the immutable PR base/head diff. Do not edit during a review pass.
- Apply required fixes as new commits, update the evidence manifest, and repeat review against the new head.
- Merge only after required checks and reviews pass. Mark `Done` only after clean post-merge verification of the merge SHA.
- Store machine-readable evidence conforming to `docs/sdlc/evidence-manifest.schema.json`.
- Follow `docs/codex/review-preflight.md` for every `cv-review-*` invocation.

## Repo Evidence

Treat these locations as authoritative evidence:

- Product and solution requirements: `solution_requirements.md`
- Architectural decisions: `docs/adr/`
- Service/package map and data flow: `docs/architecture/`
- Journey certification specs: `docs/journeys/`
- SDLC process definitions: `docs/sdlc/`
- Codex operating playbooks: `docs/codex/`

## Non-Negotiable Blockers

Block release-facing work when any in-scope change depends on:

- Runtime AI as the source of truth for compliance decisions.
- Mutable submitted packages.
- Stakeholder-specific copies of the same invoice.
- Audit evidence stored only in application logs.
- Unapproved production configuration.
- Human-authority actions performed by system or AI actors.
- Missing provenance for submitted claimed amounts.

## Review Standard

For review work, lead with findings ordered by severity and grounded in file paths, Linear fields, or evidence links. Include open questions only when they block a decision. Keep summaries secondary to risks, missing evidence, and required fixes.
