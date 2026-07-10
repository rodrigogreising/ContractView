---
name: cv-generate-implementation-tests
description: Use when Codex needs to generate or update ContractView SDLC evidence for Implementation and tests, including Linear-controlled work that needs Implementation plan, test evidence, deterministic behavior checks, and affected docs updates.
---

# Generate Implementation Tests

## Purpose

Create or update ContractView SDLC evidence for Implementation and tests. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear issue and read the relevant repo sources:

- `docs/sdlc/processes.md`
- `docs/codex/playbooks.md`
- `docs/architecture/`
- `docs/journeys/`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:implementation-tests`, `evidence:deterministic-validation`.

## Workflow

1. Implement only after the controlling Linear issue has clear SDLC stage, required evidence, and owner context.
2. Add or update tests for deterministic validation, permissions, provenance, configuration versions, journey paths, or UI behavior as applicable.
3. Update repo evidence docs when implementation changes architecture, journeys, SDLC gates, or release certification impact.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear issues needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
