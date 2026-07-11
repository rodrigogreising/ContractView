# Immutable Review Preflight

Every `cv-review-*` skill must complete this preflight before returning a review decision.

## Required Inputs

- Controlling Linear issue, parent, dependencies, status, labels, and project status.
- Issue branch and target branch.
- Pull-request URL, base SHA, and head SHA.
- Declared file scope from the Linear implementation-start comment.
- Actual immutable base/head diff.
- Machine-readable evidence manifest conforming to `docs/sdlc/evidence-manifest.schema.json`.
- Exact validation commands, exit codes, environment versions, and artifact hashes where applicable.
- Applicable `cv-review-*` AI skills derived from the affected gates and behavior.
- Certification rationale and evidence coverage for every risk/gate label.
- Explicit human-approval requirement and basis, which defaults to not required for code review.

## Blocking Conditions

Return `Blocked` without reviewing implementation claims when:

- work is on `master` or another default branch;
- the tracked worktree is dirty during review;
- there is no issue-scoped PR or immutable base/head diff;
- the PR contains unrelated or undeclared scope;
- a prerequisite is only marked Done but is not merged and post-merge verified;
- required evidence is prose-only, stale, irrelevant to the changed behavior, or does not identify the reviewed head SHA;
- required architecture, boundary, security, AI/configuration, journey, or release gates are omitted;
- an applicable `cv-review-*` AI review is missing or did not inspect the immutable diff;
- behavior changes lack proportionate unit, integration, authorization, provenance, determinism, migration, UI, Compose, or journey certification;
- a risk/gate label has no explicit evidence coverage;
- human approval is explicitly required by the issue but its decision evidence is missing.

Human code review is not a default gate. Applicable AI review skills plus
executable evidence certify code changes. A human remains necessary only for a
named governance acceptance, risk acceptance, production/configuration
activation, attestation, submission, return, approval, release signoff, or
other real-world authority decision explicitly in scope.

REC-01/SUB-57 is the sole approved legacy-baseline exception. No later issue may cite it as precedent.

## Review Discipline

1. Verify the PR base/head SHAs against the remote.
2. Compare the declared scope with the complete diff.
3. Do not edit files or change the reviewed branch during the review pass.
4. Lead with severity-ordered findings grounded in paths, diff lines, Linear fields, or evidence identifiers.
5. Return exactly one decision: `Approved`, `Approved with required fixes`, or `Blocked`.
6. Approve only when executable evidence is sufficient for the actual change; a passing but irrelevant test is a blocking evidence gap.
7. Treat required fixes as new commits. Require updated checks and evidence, then review the new immutable head.
8. Record the decision, AI review skills, reviewed base/head, findings, certification coverage, and evidence paths in Linear and the PR.

## Merge And Completion

- Merge only after all required decisions and checks pass.
- Record the merge SHA.
- Verify from clean `origin/master` using proportionate post-merge checks.
- Record post-merge commands and results in the evidence manifest and Linear.
- Move the issue to `Done` only after post-merge verification passes.
