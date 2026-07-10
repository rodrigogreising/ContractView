---
name: cv-generate-journey-certification
description: Use when Codex needs to generate or update ContractView SDLC evidence for End-to-end journey certification, including Linear-controlled work that needs Journey execution evidence with actors, preconditions, workflow path, provenance evidence, failure modes, and certification criteria.
---

# Generate Journey Certification

## Purpose

Create or update ContractView SDLC evidence for End-to-end journey certification. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear project or feature and read the relevant repo sources:

- `docs/journeys/`
- `docs/sdlc/release-certification.md`
- `docs/architecture/service-boundaries.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:journey-certification`, `evidence:journey`, `evidence:provenance`.

## Workflow

1. Map the change to one or more journey specs and update certification criteria when new certifiable behavior appears.
2. Capture version under test, fixture users, organizations, contract, budget, artifacts, configuration bundle, validation run ids, hashes, events, exceptions, and signoff needs.
3. Preserve multi-user semantics across nonprofit, agency, support/admin, auditor, and system actors.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear project or features needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
