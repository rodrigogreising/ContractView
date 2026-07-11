# SUB-58 Isolated Delivery Governance Evidence

Status: In Progress

## Purpose

SUB-58 makes issue isolation, immutable review, merge verification, and durable
evidence mandatory across ContractView's agent guidance, Linear workflow, and
review skills. It closes the process gap that allowed multiple backlog issues to
accumulate on one branch without independently reviewable PRs.

## Change Boundary

- Branch: `codex/sub-58-rec-03-delivery-governance`
- Base SHA: `44115b270e83cc03c8266a3db6c2f357cbe8a6cc`
- Controlling issue: `SUB-58`
- Project stage: `Design Review`
- Scope: agent guidance, Linear/SDLC playbooks, review skills, the backlog
  executor, evidence-manifest schema, and policy validation only.
- Runtime application behavior, database schema, and user journeys are not
  changed by this issue.

## Enforced Controls

- Exactly one leaf issue per branch and PR, except the documented SUB-57 legacy
  baseline.
- `Backlog -> Todo -> In Progress -> In Review -> Done` issue progression.
- A complete draft PR, immutable base/head diff, declared scope, and conforming
  machine-readable evidence are required before review.
- Review passes cannot edit the reviewed change. Required fixes are new commits
  followed by a new review of the new head.
- Dependents cannot begin until prerequisite PRs are merged and post-merge
  verified on `origin/master`.
- Done requires merge SHA plus clean post-merge verification.
- Authorization, configuration, provenance, immutable-submission,
  human-authority, and release work require risk-proportionate review evidence.

## Verification

The repository policy check is:

```text
python3 scripts/check_sdlc_delivery_policy.py
```

It checks the canonical controls, parses the evidence schema, verifies every
`cv-review-*` skill invokes immutable preflight, and verifies the backlog skill
retains the core prohibitions. Each changed skill is also validated with the
official skill-creator validator before review.

The executable manifest gate is:

```text
python3 scripts/validate_delivery_evidence.py --manifest <path> --phase review
python3 scripts/validate_delivery_evidence.py --manifest <path> --phase done
```

Its unit tests prove that default-branch work, mixed issue scope, missing
manifest fields, stale prerequisite proof, review-time mutation, and missing
post-merge verification are rejected. A separate negative case proves that
high-risk gate labels cannot pass without additional review evidence.

## Supersession

SUB-69 supersedes the blanket fresh-context-or-human code-review requirement.
Applicable `cv-review-*` skills are the AI code-review authority, backed by
executable certification. Human approval is reserved for explicitly named
governance and real-world authority decisions.

Exact commands, versions, exit codes, PR/base/head SHAs, and review decision are
recorded in the issue evidence manifest and Linear handoff comment before
SUB-58 enters `In Review`.
