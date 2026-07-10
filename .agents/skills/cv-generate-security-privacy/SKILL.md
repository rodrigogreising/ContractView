---
name: cv-generate-security-privacy
description: Use when Codex needs to generate or update ContractView SDLC evidence for Security, privacy, and data-governance review, including Linear-controlled work that needs Sensitive-flow review, threat model notes, mitigation list, retention decision, and accepted risks.
---

# Generate Security Privacy

## Purpose

Create or update ContractView SDLC evidence for Security, privacy, and data-governance review. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

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

Expected Linear labels: `stage:security-privacy`, `gate:security-privacy`, `risk:sensitive-data`.

## Workflow

1. Identify sensitive data classes, upload/export/integration/support paths, retention/deletion behavior, and audit export impact.
2. Record mitigations, accepted risks, owner, and release certification impact.
3. Create follow-up Linear blockers for unresolved high-risk gaps.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear project or features needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
