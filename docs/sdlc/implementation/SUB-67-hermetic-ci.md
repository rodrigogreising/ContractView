# SUB-67 Hermetic CI And Durable Evidence

Status: Build

## Control

- Issue: `SUB-67` / REC-11
- Branch: `codex/sub-67-hermetic-ci-evidence`
- Base SHA: `45964570a986f7f87b772ba73d46b17c233c915e`
- Project: ContractView / Build
- Prerequisites: SUB-57 merge `44115b270e83cc03c8266a3db6c2f357cbe8a6cc`;
  SUB-58 merge `08ae4ffef3f2ef386473149b596b6a5abbc147d8`
- Human code review: not required. The gate is issue-proportionate executable
  evidence plus applicable immutable-diff AI reviews.

## Implemented Certification Contract

- Python 3.12.13, Node 20.20.2, official GitHub Actions, Python/Node development
  dependencies, and every container base are pinned. Policy fails on drift or
  floating official Actions/container references.
- Static certification executes formatting, fatal Ruff checks, application and
  domain mypy, ontology compatibility, persistence/module/architecture/SDLC
  fitness, repository tests, frontend tests, and the production build.
- Runtime certification uses a unique Compose project with no published ports.
  It creates and destroys PostgreSQL and MinIO volumes for each of two passes,
  applies migrations/reset, runs the entire API suite, and verifies API, web,
  and worker health.
- `app.manage fingerprint` hashes only stable semantic synthetic state, omitting
  timestamps and salted password hashes. Both independent passes must match.
- CI retains service state and logs. The manifest writer derives the exact PR
  file scope from base/head, records commands, exit codes, test counts, versions,
  and timestamps, hashes retained artifacts, and validates the JSON against the
  repository evidence schema.

## Executable Evidence Before PR

- Static gate: Python 3.12.2 local-compatible runtime, pinned Node 20.20.2,
  99 typed application/script source files, 4 registries/21 contracts, 166 named persistence
  statements, 45 table owners, 6 layers/9 capabilities, 49 policy/unit tests,
  13 frontend tests, and production build all pass.
- Two-pass Compose gate: 176 API tests pass independently in each pass; API,
  web, worker, PostgreSQL, and MinIO health checks pass; both clean resets yield
  `70853fc21eadabdba8432022954b3c6008386982742b02bd48742154a0099c53`.
- Local artifacts are ignored working evidence. The GitHub run supplies the
  immutable PR-linked retained manifest and required check.

## Required Immutable AI Review

Run ADR/architecture, boundary, security/privacy, requirements traceability,
implementation/tests, Journey 11, and release-readiness reviews against the
immutable base/head diff. A passing CI label is insufficient if a review finds
semantic, security, governance, or evidence gaps. Required fixes create a new
head and repeat both CI and review.

## Completion Conditions

Before Done, configure the passing `ContractView CI / certification` context as
required on `master`, retain the schema-valid CI artifact and review manifest,
merge the approved PR, rerun clean certification at the merge SHA, and post the
merge SHA/results to Linear. REC-12 and SUB-55 remain blocked until all recovery
leaves and final journey evidence are reconciled.
