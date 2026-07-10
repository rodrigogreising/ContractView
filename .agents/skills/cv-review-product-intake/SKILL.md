---
name: cv-review-product-intake
description: Use when Codex needs to review ContractView SDLC evidence for Product intake and discovery, including Linear-controlled work before it leaves Design Review or Evidence Review or reaches Completed.
---

# Review Product Intake

## Purpose

Evaluate ContractView SDLC evidence for Product intake and discovery. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `solution_requirements.md`
- `docs/sdlc/processes.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:product-intake`.

## Workflow

1. Verify the problem, stakeholders, success metric, scope boundaries, and handoff criteria are explicit.
2. Check that the intake can map to requirements, journeys, and release evidence without guessing.
3. Flag missing owner, unclear pilot scope, or unsupported stakeholder assumptions.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up work, and whether the project may advance from its current review status.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
