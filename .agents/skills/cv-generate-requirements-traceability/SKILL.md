---
name: cv-generate-requirements-traceability
description: Use when Codex needs to generate or update ContractView SDLC evidence for Requirements traceability, including Linear-controlled work that needs Requirement-to-ADR, journey, service/package boundary, and release criterion trace.
---

# Generate Requirements Traceability

## Purpose

Create or update ContractView SDLC evidence for Requirements traceability. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `solution_requirements.md`
- `docs/adr/0001-core-architectural-pillars.md`
- `docs/journeys/`
- `docs/architecture/`
- `docs/sdlc/release-certification.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:requirements-traceability`.

## Workflow

1. Trace each material requirement to an ADR pillar, affected journey, owning service or package, and release certification criterion.
2. Record gaps as explicit missing evidence or follow-up Linear project or features rather than silent assumptions.
3. Preserve the repo docs as the durable evidence location and link them from the controlling Linear project or feature status update.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear project or features needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
