---
name: cv-review-ai-governance
description: Use when Codex needs to review ContractView SDLC evidence for AI evaluation and configuration governance review, including Linear-controlled work before it leaves Design Review or Evidence Review or reaches Completed.
---

# Review AI Governance

## Purpose

Evaluate ContractView SDLC evidence for AI evaluation and configuration governance review. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `docs/sdlc/processes.md`
- `docs/sdlc/release-certification.md`
- `docs/architecture/system-map.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`
- `docs/codex/review-preflight.md`

Expected Linear labels: `stage:ai-governance`, `gate:ai-governance`, `gate:config-governance`, `risk:ai-authority`.

## Immutable Review Preflight

Complete `docs/codex/review-preflight.md` before substantive review. This skill is an AI code reviewer. Return `Blocked` when the issue-scoped PR, clean tracked worktree, immutable base/head diff, declared scope, merged-prerequisite proof, conforming evidence manifest, or issue-proportionate executable certification is missing, stale, or irrelevant. Do not edit during the review pass. Human code review is not required; a separate human authority decision is required only when the controlling issue explicitly names one. Record the reviewed base and head SHAs in the decision.

## Workflow

1. Block runtime AI as the source of truth for submission-blocking validation, approvals, waivers, attestations, finalization, or historical reproduction.
2. Verify model, prompt, parser, evaluation, privacy, tenant-data, review threshold, and human correction evidence exists.
3. Check configuration governance for draft, tested, approved, active, superseded, and retired states where applicable.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up work, and whether the project may advance from its current review status.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
