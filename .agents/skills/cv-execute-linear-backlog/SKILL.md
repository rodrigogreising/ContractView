---
name: cv-execute-linear-backlog
description: Execute, resume, or complete explicitly scoped unfinished ContractView Linear stories, epics, or projects through the repository's isolated branch, pull-request, executable-evidence, AI-review, merge, and post-merge SDLC. Use when asked to start, continue, resume, or finish ContractView work controlled by Linear, including when the user explicitly requests a persistent goal.
---

# Execute ContractView Linear Delivery

## Objective

Deliver the declared Linear scope one dependency-ready leaf story at a time while preserving ContractView's project-status control plane, durable repo evidence, isolated PRs, executable certification, and immutable AI review.

## Establish Scope

1. Read `AGENTS.md`, `docs/codex/playbooks.md`, `docs/codex/sdlc-linear-control-plane.md`, `docs/sdlc/linear-workflow.md`, `docs/codex/review-preflight.md`, and `docs/sdlc/evidence-manifest.schema.json` completely.
2. Read the controlling Linear project, latest status update, named issue or epic, parents, children, dependencies, acceptance criteria, labels, linked repo evidence, and current goal.
3. Resolve scope in this order:
   - issue, epic, project, or issue set explicitly named in the invocation;
   - the active persistent goal's declared scope;
   - a Linear epic or project explicitly identified as the active workstream.
4. Treat an unqualified request for "all outstanding issues" as all unfinished, non-canceled leaves only when the invocation also identifies the project or epic. Otherwise request the missing scope before mutation.
5. Snapshot the in-scope issue IDs, exclusions, dependency graph, and terminal acceptance condition in Linear. Never absorb newly created or unrelated backlog silently.
6. Create a persistent goal only when the user explicitly asks to set a goal, continue autonomously, or complete a scope. Derive the objective from the declared scope and terminal evidence. Do not replace a different active goal without user direction.

Use this goal form when requested:

`Complete <Linear scope> through isolated, reviewed, merged PRs and post-merge verification until every in-scope non-canceled leaf and required terminal certification is approved.`

## Control Project State

1. Use the Linear project status as the SDLC stage and the repo as the durable evidence store.
2. If new work begins after `Completed`, preserve the prior completion record and post a status update before moving the project to the stage required by the new scope.
3. Use:
   - `Discovery` for product intake, scope, stakeholders, outcomes, and success criteria;
   - `Design Review` for requirements, ADR, architecture, boundaries, security/privacy, AI/configuration governance, and journey design;
   - `Build` for approved implementation work;
   - `Evidence Review` for terminal journey, provenance, security, configuration, and release evidence;
   - `Rollout` only for an explicitly authorized deployment or staged release;
   - `Completed` only when the declared project scope needs no further action.
4. Do not call a shared project `Completed` while unfinished non-canceled project work remains unexplained. Separate or explicitly exclude future work in Linear before a terminal project decision.
5. Post project status updates when generation starts, artifacts change, review starts, findings return, fixes land, a gate advances, or work becomes blocked.

## Select One Story

1. Refresh every in-scope issue and relation before selection.
2. Exclude completed, canceled, duplicate, and parent-only aggregation issues from implementation selection.
3. A leaf is dependency-ready only when every blocker is `Done`, its PR merge SHA is an ancestor of `origin/master`, and its post-merge evidence is recorded. A Linear status alone is insufficient.
4. Move a dependency-ready leaf from `Backlog` to `Todo`. Select exactly one `Todo` leaf by blocker severity, Linear priority, dependency depth, then creation time.
5. Implement a parent only when it has distinct acceptance criteria that require its own artifact. Otherwise close it only after all required children and terminal evidence are complete.
6. If an old `Done` issue lacks merged or post-merge proof, create or use an explicit remediation story; do not treat history as evidence or silently rewrite it.

## Start The Story

1. Require GitHub access, a clean tracked worktree, current repository default branch, and a fast-forward update from its remote. Stop before mutation for unrelated user changes.
2. Create the Linear branch or `codex/<issue>-<slug>` from the verified remote default-branch SHA. Never implement on the default branch.
3. Move the issue to `In Progress` and post:
   - branch and base SHA;
   - project status;
   - generation and review skills;
   - declared file scope;
   - merged prerequisites and evidence;
   - implementation plan;
   - expected evidence-manifest path;
   - human-approval requirement and basis.
4. Derive applicable skills from acceptance criteria, stage labels, gate/risk labels, behavior, and affected durable evidence. Invoke every applicable generation skill:
   - product intake;
   - requirements traceability;
   - ADR/architecture;
   - boundary review;
   - security/privacy;
   - AI/configuration governance;
   - implementation/tests;
   - journey certification;
   - release readiness;
   - operations/postmortem.
5. Read each selected skill completely and follow it. Do not default cross-cutting work to implementation/tests only.

## Implement And Certify

1. Implement only the selected story's complete acceptance criteria and declared scope.
2. Add issue-proportionate unit, integration, authorization, provenance, determinism, boundary, migration, frontend, Compose, journey, and artifact checks.
3. Update affected ADR, architecture, journey, security/privacy, AI-governance, implementation, traceability, operations, and release evidence.
4. Run focused and regression checks. Store machine-readable evidence conforming to `docs/sdlc/evidence-manifest.schema.json`, including immutable base/head SHAs, commands, exit codes, versions, timestamps, test counts, certification rationale, risk/gate coverage, and artifact hashes.
5. Commit with the issue identifier, push, and open a draft PR against the repository default branch.
6. Post PR URL, base/head SHA, checks, manifest, risks, and dependency impact to Linear; then move the issue to `In Review`.

## Review, Merge, And Finish

1. Complete `docs/codex/review-preflight.md` against the immutable remote base/head diff with a clean worktree. Do not edit during a review pass.
2. Run every applicable `cv-review-*` skill corresponding to the generation skills and changed risks/gates.
3. Treat every applicable `cv-review-*` skill as an AI code reviewer.
4. Require one decision per review: `Approved`, `Approved with required fixes`, or `Blocked`. Human code review is not a default gate; require human approval only for an explicitly named governance or real-world authority decision.
5. Apply required fixes as new commits on the same issue PR, regenerate evidence, and repeat immutable review.
6. Merge only after required CI and reviews pass.
7. Verify the merge SHA from clean, current remote default-branch state with proportionate post-merge checks. Record commands, exit codes, evidence paths/hashes, remaining risks, and newly unblocked dependents in Linear.
8. Move the story to `Done` only after merge and post-merge verification. Refresh the dependency graph and select the next in-scope leaf.
9. Complete a parent or persistent goal only when:
   - every in-scope non-canceled leaf is merged and post-merge verified;
   - required parent acceptance criteria are proven;
   - required terminal journey/release evidence is retained and approved;
   - Linear project/epic state and final status update match the declared scope.
10. Mark a persistent goal blocked only under the platform's repeated-blocker rule. Otherwise retain it across continuations.

## Prohibitions

- Do not implement directly on `master`.
- Treat another configured repository default branch with the same prohibition.
- Do not combine multiple leaf issues in one PR or stage unrelated files.
- No dependent work before prerequisite merge and post-merge verification.
- No prose-only test evidence for executable behavior.
- No self-approval without an immutable remote diff and applicable AI review skills.
- Do not move issues to `Done` before merge and post-merge verification.
- No bypass of architecture, boundary, security, governance, journey, operations, or release skills.
- No silent scope expansion, acceptance-criteria reduction, test-only authority path, or manual state mutation to maintain momentum.
- No goal completion based only on Linear statuses or a passing happy path.
