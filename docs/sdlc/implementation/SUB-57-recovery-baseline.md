# SUB-57 Recovery Baseline Evidence

Status: In Progress

## Purpose

This issue is the single approved exception to the issue-isolated PR rule. It
preserves legacy work that accumulated before ContractView adopted immutable
branch, PR, review, merge, and post-merge evidence gates.

## Git Baseline

- Base branch: `master`
- Base SHA: `2d7bc4a`
- Recovery branch: `codex/recovery-baseline`
- Remote baseline: `origin/master` at `2d7bc4a`
- Generated `tmp/` PDF render artifacts are explicitly excluded.

The preserved working tree contains the unfinished SUB-46/SUB-49 UI and SDLC
evidence plus the initial `cv-execute-linear-backlog` skill. These changes are
accepted only as a legacy-baseline import. REC-12 will reconcile their prior
issue claims against the repaired architecture and merged evidence.

## Verification

- `git diff --check`: passed.
- Targeted secret-pattern scan: passed with no findings.
- Skill validator: `Skill is valid!`.
- Frontend runtime: Node `v24.14.0`.
- Frontend test: 1 file and 9 tests passed.
- Frontend production build: passed.
- Clean `docker compose down -v` and `docker compose up -d --build`: passed.
- PostgreSQL, MinIO, API, worker, and web reached healthy state.
- Deterministic synthetic reset: passed.
- API suite with the worker stopped: 70 passed.

## Known Recovery Findings

Running the API suite while the normal worker is live is not hermetic: the
worker races tests for queued jobs. The clean run initially produced 60 passes
and 10 setup errors before the worker was stopped, the fixture state reset, and
the suite rerun successfully. REC-11 owns isolated test orchestration so the
documented test command cannot race runtime services.

Git push may succeed through the configured Git credential path, but GitHub CLI
authentication is invalid at the time of this evidence. PR creation and review
remain blocked until GitHub access is restored or the connected GitHub app can
access the repository.

## Review Constraint

No later recovery issue may reuse this exception. Every REC-02 through REC-12
leaf change must have an issue branch, immutable base/head diff, draft PR,
required review decisions, merge SHA, and clean post-merge verification.
