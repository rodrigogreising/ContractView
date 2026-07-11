---
name: cv-review-implementation-tests
description: Use when Codex needs to review ContractView SDLC evidence for Implementation and tests, including Linear-controlled work before it leaves Design Review or Evidence Review or reaches Completed.
---

# Review Implementation Tests

## Purpose

Evaluate ContractView SDLC evidence for Implementation and tests. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `docs/sdlc/processes.md`
- `docs/codex/playbooks.md`
- `docs/architecture/`
- `docs/journeys/`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`
- `docs/codex/review-preflight.md`

Expected Linear labels: `stage:implementation-tests`, `evidence:deterministic-validation`.

## Immutable Review Preflight

Complete `docs/codex/review-preflight.md` before substantive review. Return `Blocked` when the issue-scoped PR, clean tracked worktree, immutable base/head diff, declared scope, merged-prerequisite proof, or conforming evidence manifest is missing. Do not edit during the review pass. Record the reviewed base and head SHAs in the decision.

## Workflow

1. Review code, tests, and docs against the controlling Linear project or feature and affected SDLC gates.
2. Flag missing automated tests, missing journey evidence, unlinked repo docs, and behavior that bypasses boundaries or human authority.
3. Confirm the Linear project or feature includes test result links or explicit test gaps.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up work, and whether the project may advance from its current review status.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
