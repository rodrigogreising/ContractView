---
name: cv-execute-linear-backlog
description: Execute or resume outstanding ContractView Linear recovery and POC issues through the repository's isolated branch, pull-request, review, merge, and evidence workflow. Use when asked to start, continue, resume, or complete the ContractView backlog, recovery program, Journey 11, or SUB-55.
---

# Execute ContractView Linear Backlog

## Objective

Complete the ContractView recovery program and all remaining dependency-ready POC issues through isolated, reviewed, merged PRs until SUB-55 passes and is approved.

## Start Or Resume

1. Read `AGENTS.md`, `docs/codex/playbooks.md`, `docs/codex/sdlc-linear-control-plane.md`, `docs/sdlc/linear-workflow.md`, `docs/codex/review-preflight.md`, and `docs/sdlc/evidence-manifest.schema.json` completely.
2. Read the ContractView Linear project, its current status update, and outstanding issues on team `Substrate`.
3. Call `get_goal`. If no active goal exists, call `create_goal` with the objective above. Continue an existing matching goal instead of replacing it.
4. Inspect `git status -sb`, current branch, `origin`, GitHub authentication, and remote default branch.
5. Stop before mutation when the worktree contains unrelated user changes or GitHub access prevents the required issue branch and PR workflow. Record the blocker in Linear without weakening the protocol.

## Select Work

1. Prefer SUB-56 recovery children until REC-12 is complete, then resume the original backlog.
2. Select exactly one dependency-ready leaf issue at a time.
3. Treat a prerequisite as complete only when its PR is merged into `origin/master` and its post-merge evidence is recorded. A Linear `Done` state alone is insufficient.
4. Rank eligible issues by blocker severity, Linear priority, dependency depth, then creation time.
5. Do not implement parent aggregation issues directly unless their acceptance criteria require a distinct artifact.

## Execute One Issue

1. Update local `master` from `origin/master` with a fast-forward-only pull and require a clean worktree.
2. Create the Linear-generated branch or `codex/<issue>-<slug>` from the verified base SHA.
3. Move the issue to `In Progress` and post the branch, base SHA, applicable generation and review skills, plan, declared file scope, dependencies, and expected evidence.
4. Invoke every applicable `cv-generate-*` skill. Do not default architecture, security, AI/configuration, provenance, or release work to implementation-only evidence.
5. Implement the complete issue acceptance criteria without unrelated changes.
6. Add proportionate unit, integration, authorization, provenance, determinism, boundary, migration, and UI tests.
7. Update durable ADR, architecture, journey, security/privacy, AI-governance, implementation, traceability, and release evidence when affected.
8. Run focused and regression checks. Write a machine-readable evidence manifest conforming to `docs/sdlc/evidence-manifest.schema.json`, including base/head SHA, commands, exit codes, environment versions, timestamps, test counts, and artifact hashes.
9. Commit with the issue identifier, push the branch, and open a draft PR against `master`.
10. Post the PR URL and head SHA to Linear, then move the issue to `In Review`.

## Review And Merge

1. Complete `docs/codex/review-preflight.md`, then run every applicable `cv-review-*` skill against the immutable PR base/head diff. Do not edit files during the review pass.
2. Require a fresh-context or human review for authorization, configuration activation, provenance, immutable submission, human authority, and release gates.
3. If the decision is `Approved with required fixes`, apply fixes as new commits, rerun checks, update evidence, and repeat review.
4. Merge only after required CI passes and all required review decisions are `Approved` or explicitly non-blocking.
5. Verify the merge SHA from a clean checkout and clean Docker Compose state as proportionate to the issue.
6. Post merge SHA, exact verification results, durable evidence paths, risks, and dependency impact to Linear. Only then move the issue to `Done`.
7. Refresh project status and dependencies, then continue with the next eligible issue.

## Project Gates

- Keep the ContractView project in `Design Review` until REC-02 and REC-03 are approved, merged, and verified.
- Use `Build` for implementation after design gates pass.
- Use `Evidence Review` for REC-12, Journey 11, and release evidence assembly.
- Do not mark the persistent goal complete until SUB-55 is merged, Journey 11 passes from clean Docker Compose, video/trace/screenshots and machine-readable results are retained, and release review is approved.
- Mark the goal blocked only under the platform's repeated-blocker policy. Otherwise persist across continuations.

## Prohibitions

- Do not implement directly on `master`.
- Do not combine multiple leaf issues in one PR; REC-01 is the sole documented legacy exception.
- Do not stage unrelated files or generated `tmp/` artifacts.
- Do not start dependents before prerequisite merge verification.
- Do not accept prose-only test evidence.
- Do not self-approve without an immutable diff.
- Do not move issues to `Done` before merge and post-merge verification.
- Do not bypass required architecture, boundary, security, governance, journey, or release skills.
- Do not reduce acceptance criteria to maintain momentum.
