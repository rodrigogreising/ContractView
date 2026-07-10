---
name: cv-generate-product-intake
description: Use when Codex needs to generate or update ContractView SDLC evidence for Product intake and discovery, including Linear-controlled work that needs Problem statement, impacted stakeholders, success metric, and in/out of scope.
---

# Generate Product Intake

## Purpose

Create or update ContractView SDLC evidence for Product intake and discovery. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear issue and read the relevant repo sources:

- `solution_requirements.md`
- `docs/sdlc/processes.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:product-intake`.

## Workflow

1. Define the problem, affected users, pilot or release context, success metric, in scope items, and out of scope items.
2. Map the intake to at least one ContractView lifecycle stage and identify likely affected journeys or architecture areas.
3. If the request is not clear enough to map to requirements and journeys, stop with the missing decisions instead of fabricating scope.
4. Update the Linear issue with generated artifact paths and any blockers.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear issues needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
