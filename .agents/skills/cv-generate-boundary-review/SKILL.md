---
name: cv-generate-boundary-review
description: Use when Codex needs to generate or update ContractView SDLC evidence for Service/package boundary review, including Linear-controlled work that needs Service or package ownership, dependency, data, event, configuration, deterministic behavior, and prohibited-responsibility checklist.
---

# Generate Boundary Review

## Purpose

Create or update ContractView SDLC evidence for Service/package boundary review. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear issue and read the relevant repo sources:

- `docs/architecture/service-boundaries.md`
- `docs/architecture/system-map.md`
- `packages/README.md`
- `services/README.md`
- `apps/README.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:boundary-review`, `gate:architecture`.

## Workflow

1. Declare the owner role, responsibilities, data owned, allowed dependencies, events emitted, configuration consumed, deterministic requirements, human authority boundary, and prohibited responsibilities.
2. Use shared packages for contracts, not hidden service dependencies.
3. Link the boundary artifact from the Linear issue and add gate labels when ownership or dependencies change.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear issues needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
