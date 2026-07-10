---
name: cv-review-operations-postmortem
description: Use when Codex needs to review ContractView SDLC evidence for Production operation, incident response, and postmortems, including Linear-controlled work before it leaves In Review or reaches Done.
---

# Review Operations Postmortem

## Purpose

Evaluate ContractView SDLC evidence for Production operation, incident response, and postmortems. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear issue and read the relevant repo sources:

- `docs/sdlc/processes.md`
- `docs/sdlc/release-certification.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:operations-postmortem`, `evidence:runbook`.

## Workflow

1. Verify runbooks or postmortems cover owner, trigger, detection, mitigation, recovery, evidence, and corrective action tracking.
2. Flag missing audit/export, retention, support-access, integration-failure, backup/restore, or incident-response coverage where in scope.
3. Check corrective actions are linked to Linear issues and relevant docs/tests are updated.

## Output

Return:

- Decision: Approved, Approved with required fixes, or Blocked.
- Findings first, ordered by severity, with concrete repo path or Linear field references.
- Required fixes, follow-up issues, and whether the issue may advance from In Review.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
