---
name: cv-generate-release-readiness
description: Use when Codex needs to generate or update ContractView SDLC evidence for Release readiness and evidence signoff, including Linear-controlled work that needs Release certification record with decision, evidence links, exceptions, risks, and signoff.
---

# Generate Release Readiness

## Purpose

Create or update ContractView SDLC evidence for Release readiness and evidence signoff. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear issue and read the relevant repo sources:

- `docs/sdlc/release-certification.md`
- `docs/sdlc/processes.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:release-readiness`, `gate:release-certification`.

## Workflow

1. Assemble requirements trace, ADRs, architecture updates, tests, journey results, configuration versions, provenance exports, security/privacy review, AI evaluation, operational runbooks, known risks, and exceptions.
2. Use exactly one decision: Certified, Certified with exceptions, or Blocked.
3. Each exception must identify owner, risk, compensating control, target resolution, and pilot safety impact.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear issues needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
