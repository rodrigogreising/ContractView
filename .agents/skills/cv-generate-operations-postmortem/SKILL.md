---
name: cv-generate-operations-postmortem
description: Use when Codex needs to generate or update ContractView SDLC evidence for Production operation, incident response, and postmortems, including Linear-controlled work that needs Runbook, incident record, timeline, impact, root cause, corrective actions, and evidence-retention updates.
---

# Generate Operations Postmortem

## Purpose

Create or update ContractView SDLC evidence for Production operation, incident response, and postmortems. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `docs/sdlc/processes.md`
- `docs/sdlc/release-certification.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:operations-postmortem`, `evidence:runbook`.

## Workflow

1. Create or update runbooks for in-scope jobs, queues, retries, dead letters, integrations, support access, audit export, incident response, backup, restore, retention, or deletion.
2. For incidents, record timeline, impact, root cause, corrective actions, owners, and linked follow-up Linear project or features.
3. Update docs or tests when an incident reveals an SDLC or certification evidence gap.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear project or features needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
