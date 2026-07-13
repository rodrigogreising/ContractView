# SUB-55 Final POC Certification

## Control Plane

- Issue: `SUB-55` / REL-01.
- Parent: `SUB-22`.
- Project stage: Evidence Review.
- Branch: `codex/sub-55-final-poc-certification`.
- Base SHA: `c8c4d1773db1abb01857e9f27c18887a25c9d882`.
- Prerequisites: SUB-66, SUB-50, SUB-26, and SUB-53 are merged and
  post-merge verified.
- Human approval: not required for code review or synthetic development POC
  certification. Staging/production promotion remains separate and human.

## Scope And Architecture Decision

SUB-55 is the terminal evidence and release issue. It adds a shared web
identity header that displays an explanatory permission summary for the closed
five-role vocabulary, extends unit/browser assertions, and updates durable
release evidence. The summary is not an authorization input. Server
application policy, canonical assignments, resource ownership, lifecycle
state, and target version remain authoritative.

No new ADR, runtime layer, capability owner, table, migration, API path,
provider, configuration primitive, or deployment is required. The Playwright
harness remains an external client of public web/API surfaces.

## Acceptance Trace

| Acceptance criterion | Executable evidence |
| --- | --- |
| Every Journey 11 step uses visible UI paths | One canonical Playwright scenario drives configuration through final audit; no internal import, database edit, test endpoint, or role switch |
| Every persona shows identity and permissions | Shared header unit coverage plus exact Playwright assertions for user, organization, role, bounded permission summary, and logout |
| Real processing and complete lifecycle | Worker-backed ingestion/extraction and visible correction, deterministic validation, attestation, packages, submission, return, revision, resubmission, approval, and audit |
| Provenance, determinism, and immutable versions | Typed events/relations/snapshots; validation and package replay; captured unchanged v1 and distinct v2 hashes in the audit trail |
| Forbidden commands fail without mutation | Direct browser-context `403` assertions plus authorization/zero-mutation integration suite |
| Clean retained certification | Isolated Compose headless and default 650 ms headed runs retain JSON, trace, video, screenshots, HTML, runtime logs, service state, versions, commands, counts, and SHA-256 hashes |

## Required Checks

The immutable candidate must pass:

1. `bash scripts/ci/run_static.sh`.
2. `bash scripts/ci/run_hermetic.sh <evidence-directory>` twice over fresh
   state with an equal reset fingerprint.
3. `make journey11-headless EVIDENCE_DIR=<evidence-directory>`.
4. `make journey11-headed EVIDENCE_DIR=<evidence-directory>` with the default
   `650 ms` pacing.
5. Hosted `ContractView CI / certification` for the exact PR head.
6. Schema/policy validation of the PR evidence manifest.
7. Eight immutable-diff AI review skills with no review-time edits.
8. Clean post-merge static, hermetic, and Journey 11 certification at the
   exact merge SHA.

## Candidate Evidence

Local candidate decision: ready for immutable PR certification. Final release
decision remains pending the exact PR-head hosted run, eight AI reviews, merge,
and clean post-merge verification.

- Static/policy/unit/frontend/build: 78 repository tests plus 24 frontend tests
  (102 total), type checks over 106 Python sources, 34 shared contracts, 47
  owned tables, and 177 named persistence statements.
- Hermetic Compose: 189 API tests per isolated pass / 378 executions, with
  equal reset fingerprint
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- Clean headless Journey 11: one expected, zero unexpected/flaky in 10.96s;
  result `72fa2f26374546ae374377ac0890e2943946aa00dba43d22e3796d6021256fce`,
  trace `800283c55889177be50431bc4fcbe34357f25f9f2973a2ed08e016b842c0dd95`,
  video `4c6f4394c5dd27eed5eed841cfc20dc28fb19d38bf43f884d8a0dcfd50637d0a`,
  and 13 screenshots.
- Default 650 ms paced headed Journey 11: one expected, zero
  unexpected/flaky in 60.25s; result
  `9ca5710fbf8df20080050a0e86bb19711570afc6d1c4a562fa69daa4787d7a04`,
  trace `3b388d4db69d151e60e30d6ae10cb824e54c7bd8ef85e79d6b8112886cf4cd79`,
  video `86801b1feb1f05399592fada50555cb772b8c56f4a383439dabc6bb53548d542`,
  and 13 screenshots.
- Both browser modes asserted the exact visible name, organization, role,
  bounded permission summary, and logout for every persona while executing the
  same complete lifecycle.

Local machine evidence is retained under ignored `tmp/evidence/SUB-55/`.
Hosted evidence is retained by the certification run and linked from Linear.
Exact PR SHAs, hosted artifact hashes, review decisions, merge SHA, and the
terminal release decision must be posted before completion.

## Release Boundaries And Exceptions

- Runtime data and retained media are synthetic and non-branded only.
- The local adapter supports one synthetic document class and produces draft
  values only.
- Real identity lifecycle, malware scanning, hosted retention/recovery, real
  data, payments, notifications, and production deployment remain excluded.
- Public full history/identity, all-rights-reserved licensing, and disabled
  hosted secret scanning remain explicit owner-accepted disclosure exceptions
  with repository scanning as a compensating control.
- These exceptions do not weaken tenant authorization, deterministic rules,
  immutable evidence, or human-authority requirements.
