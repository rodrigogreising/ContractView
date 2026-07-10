---
name: cv-review-boundary-review
description: Use when Codex needs to review ContractView SDLC evidence for Service/package boundary review, including Linear-controlled work before it leaves Design Review or Evidence Review or reaches Completed.
---

# Review Boundary Review

## Purpose

Evaluate ContractView SDLC evidence for Service/package boundary review. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

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

1. Verify no service imports another service internal implementation or mutates another owner boundary.
2. Check reporting remains a projection, UI does not replace server-side permission checks, and AI does not perform compliance authority.
3. Flag missing event, configuration, deterministic, or human-authority evidence.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up work, and whether the project may advance from its current review status.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
