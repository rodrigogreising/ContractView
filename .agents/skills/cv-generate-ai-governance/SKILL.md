---
name: cv-generate-ai-governance
description: Use when Codex needs to generate or update ContractView SDLC evidence for AI evaluation and configuration governance review, including Linear-controlled work that needs AI intended use, prohibited authority, model/prompt/parser versions, evaluation plan, metrics, and human-review rules.
---

# Generate AI Governance

## Purpose

Create or update ContractView SDLC evidence for AI evaluation and configuration governance review. Linear controls status, ownership, blockers, labels, and handoffs; repo docs remain the durable evidence source.

## Required Context

Before acting, identify the controlling Linear issue and read the relevant repo sources:

- `docs/sdlc/processes.md`
- `docs/sdlc/release-certification.md`
- `docs/architecture/system-map.md`
- `docs/codex/playbooks.md`
- `docs/sdlc/README.md`
- `docs/sdlc/processes.md`
- `docs/sdlc/linear-workflow.md`
- `docs/codex/sdlc-linear-control-plane.md`

Expected Linear labels: `stage:ai-governance`, `gate:ai-governance`, `gate:config-governance`, `risk:ai-authority`.

## Workflow

1. Document intended use, prohibited authority, source evidence requirements, model/prompt/parser versions, evaluation set, metrics, confidence thresholds, and human correction path.
2. Make configuration lifecycle explicit when AI suggests schemas, mappings, rules, workflows, views, templates, or bundles.
3. Frame AI as draft-producing or advisory unless approved deterministic software owns the compliance decision.

## Output

Return:

- Updated repo artifact path or explicit missing-decision list.
- Linear comment text with generated artifact path, blockers, and next review skill.
- Follow-up Linear issues needed for unresolved gates.

When evidence is incomplete, name the missing artifact or decision directly instead of inventing facts.
