---
name: cv-review-journey-certification
description: Use when Codex needs to review ContractView SDLC evidence for End-to-end journey certification, including Linear-controlled work before it leaves Design Review or Evidence Review or reaches Completed.
---

# Review Journey Certification

## Purpose

Evaluate ContractView SDLC evidence for End-to-end journey certification. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `docs/journeys/`
- `docs/sdlc/release-certification.md`
- `docs/architecture/service-boundaries.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`
- `docs/codex/review-preflight.md`

Expected Linear labels: `stage:journey-certification`, `evidence:journey`, `evidence:provenance`.

## Immutable Review Preflight

Complete `docs/codex/review-preflight.md` before substantive review. Return `Blocked` when the issue-scoped PR, clean tracked worktree, immutable base/head diff, declared scope, merged-prerequisite proof, or conforming evidence manifest is missing. Do not edit during the review pass. Record the reviewed base and head SHAs in the decision.

## Workflow

1. Verify the journey evidence proves both user-visible behavior and evidence quality.
2. Flag missing actors, preconditions, workflow path, provenance, failure modes, certification criteria, or signoff.
3. Block release-facing claims when certified journeys cannot be reconstructed.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up work, and whether the project may advance from its current review status.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
