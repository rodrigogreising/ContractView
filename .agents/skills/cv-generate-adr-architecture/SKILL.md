---
name: cv-generate-adr-architecture
description: Use when Codex needs to generate or update ContractView SDLC evidence for Architecture and ADR review, including Linear-controlled work that needs ADR draft or amendment plus architecture impact summary.
---

# Generate ADR And Architecture

## Purpose

Create or update ContractView SDLC evidence for Architecture and ADR review. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear issue and read the relevant repo sources:

- `docs/adr/`
- `docs/architecture/system-map.md`
- `docs/architecture/data-flow.md`
- `docs/architecture/domain-model.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:adr-architecture`, `gate:adr`, `gate:architecture`.

## Workflow

1. Decide whether the change requires a new ADR, an ADR amendment, or an explicit no-ADR rationale.
2. Update architecture-facing artifacts for material changes to service shape, data ownership, provenance, configuration, validation, human authority, or AI responsibility.
3. Keep architecture language declarative until implementation frameworks are selected.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear issues needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
