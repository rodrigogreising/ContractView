---
name: cv-review-security-privacy
description: Use when Codex needs to review ContractView SDLC evidence for Security, privacy, and data-governance review, including Linear-controlled work before it leaves Design Review or Evidence Review or reaches Completed.
---

# Review Security Privacy

## Purpose

Evaluate ContractView SDLC evidence for Security, privacy, and data-governance review. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `docs/sdlc/processes.md`
- `docs/architecture/data-flow.md`
- `docs/architecture/service-boundaries.md`
- `docs/sdlc/release-certification.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`
- `docs/codex/review-preflight.md`

Expected Linear labels: `stage:security-privacy`, `gate:security-privacy`, `risk:sensitive-data`.

## Immutable Review Preflight

Complete `docs/codex/review-preflight.md` before substantive review. This skill is an AI code reviewer. Return `Blocked` when the issue-scoped PR, clean tracked worktree, immutable base/head diff, declared scope, merged-prerequisite proof, conforming evidence manifest, or issue-proportionate executable certification is missing, stale, or irrelevant. Do not edit during the review pass. Human code review is not required; a separate human authority decision is required only when the controlling issue explicitly names one. Record the reviewed base and head SHAs in the decision.

## Workflow

1. Verify sensitive data flows, support access, retention, deletion, legal hold, export, and integration paths are covered where in scope.
2. Flag unmitigated high-risk gaps, missing owner acceptance, or evidence stored outside retention policy.
3. Check risk and gate labels match the review scope.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up work, and whether the project may advance from its current review status.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
