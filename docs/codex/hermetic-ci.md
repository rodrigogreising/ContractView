# Hermetic CI And Evidence Runbook

## Purpose

SUB-67 makes every ContractView pull request certifiable from pinned tools,
isolated runtime state, executable checks, and retained machine evidence. The
required check is `ContractView CI / certification`.

## Local Static Certification

Use Python 3.12 and the Node version in `.nvmrc`, install both pinned
requirements files, and run:

```bash
bash scripts/ci/run_static.sh
```

This checks tool support, formatting, fatal Python lint, application/domain
types, shared-contract compatibility, persistence statements, module ownership,
architecture policy, delivery policy, repository tests, frontend tests, and the
production build.

## Local Hermetic Runtime Certification

```bash
CI_PROJECT_NAME=contractview-ci-local bash scripts/ci/run_hermetic.sh artifacts/ci
```

The script creates and destroys a uniquely named Compose project twice. Each
pass uses new PostgreSQL and MinIO volumes, applies numbered migrations, resets
synthetic fixtures, runs the full API suite, and verifies API, web, and worker
health. Different reset fingerprints fail the run. Cleanup runs on success or
failure.

## Retained Evidence

GitHub CI writes `artifacts/ci/manifest.json` after successful PR checks and
uploads the directory for 30 days. The manifest conforms to
`docs/sdlc/evidence-manifest.schema.json` and records:

- immutable PR base/head SHAs and the exact changed-file scope;
- machine-validated prerequisite issue, merge-SHA, and post-merge proofs;
- pinned environment versions and exact commands/exit codes;
- test counts, timestamps, service-state artifacts, and SHA-256 hashes;
- the applicable AI review skills and release-gate coverage.

Logs must contain only synthetic test/runtime information. Do not retain
secrets, cookies, document bodies, database dumps, or real data.

## Merge Gate

The branch protection rule requires the CI context after the first successful
run establishes it. Applicable AI reviews inspect the immutable base/head diff
without editing. Required fixes are new commits followed by a new CI run and a
repeated review. Done requires clean verification of the merge SHA; passing CI
alone does not complete Journey 11 or SUB-55.

Immediately before review approval and merge, an authenticated operator records
the external GitHub protection state without retaining API URLs or credentials:

```bash
python3 scripts/ci/capture_branch_protection.py \
  --repository rodrigogreising/ContractView \
  --output artifacts/ci/branch-protection.json
```

The command fails unless `master` strictly requires `certification`, enforces
the check for administrators, and prohibits force pushes and deletion. Retain
the sanitized file and SHA-256 with the immutable review evidence because a
repository visibility transition can reset GitHub branch protection.
