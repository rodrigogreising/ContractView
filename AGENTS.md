# ContractView Codex Guidance

ContractView uses Linear as the SDLC control plane and this repository as the durable evidence store. Before material work, identify the controlling Linear issue, the SDLC stage, and the repo evidence that must be created or reviewed.

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

- Use Linear for workflow state, ownership, priority, due date, blockers, labels, and handoff comments.
- Use the `Substrate` Linear team and `ContractView` Linear project unless the user explicitly chooses another target.
- Do not rely on custom Linear statuses. Use `Backlog`, `Todo`, `In Progress`, `In Review`, `Done`, `Duplicate`, and `Canceled`.
- Every material SDLC child issue must include the SDLC control, traceability, and review result sections defined in `docs/codex/sdlc-linear-control-plane.md`.
- Comment on the Linear issue when generation starts, when artifacts are updated, when review starts, when findings are returned, when fixes are applied, and when the issue is ready for the next gate or blocked.

## Skill Invocation

- Use the matching `cv-generate-*` skill to create or update SDLC evidence.
- Use the matching `cv-review-*` skill before moving a Linear issue out of `In Review` or considering it `Done`.
- Review skills must return one decision: `Approved`, `Approved with required fixes`, or `Blocked`.
- If evidence is missing, name the missing artifact or decision directly rather than inventing it.

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
