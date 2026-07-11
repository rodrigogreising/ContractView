---
name: cv-review-release-readiness
description: Use when Codex needs to review ContractView SDLC evidence for Release readiness and evidence signoff, including Linear-controlled work before it leaves Design Review or Evidence Review or reaches Completed.
---

# Review Release Readiness

## Purpose

Evaluate ContractView SDLC evidence for Release readiness and evidence signoff. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `docs/sdlc/release-certification.md`
- `docs/sdlc/processes.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`
- `docs/codex/review-preflight.md`

Expected Linear labels: `stage:release-readiness`, `gate:release-certification`.

## Immutable Review Preflight

Complete `docs/codex/review-preflight.md` before substantive review. Return `Blocked` when the issue-scoped PR, clean tracked worktree, immutable base/head diff, declared scope, merged-prerequisite proof, or conforming evidence manifest is missing. Do not edit during the review pass. Record the reviewed base and head SHAs in the decision.

## Workflow

1. Check every release certification gate has required evidence or an explicit exception.
2. Block if any non-negotiable blocker is in scope: runtime AI compliance authority, mutable submitted packages, stakeholder-specific invoice copies, application-log-only audit trail, unapproved production configuration, AI/system human-authority actions, or missing provenance.
3. Verify final signoff roles and Linear release impact are recorded.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up work, and whether the project may advance from its current review status.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
