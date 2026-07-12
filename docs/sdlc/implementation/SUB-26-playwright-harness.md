# SUB-26 Implementation Evidence: Canonical Playwright Harness

Status: Implementation complete; immutable PR review pending

## Scope And Decision

SUB-26 makes Journey 11 executable through the public web application. A
single Playwright scenario starts from the supported deterministic reset, uses
normal server-issued login/logout for all five seeded personas, and performs
configuration activation, ingestion, worker processing, extraction review,
deterministic validation, attestation, packaging, submission, return,
correction, resubmission, approval, and audit reconstruction.

The harness adds no test endpoint, database edit, role-switch shortcut, client
authority, deployable, table owner, or runtime AI decision. It runs against an
isolated Compose project on a private test port and starts the worker only after
the reset completes so worker health cannot race schema replacement.

## Acceptance Evidence

- Each authenticated workspace visibly proves user, organization, role, and
  logout. The scenario logs out before authenticating the next persona.
- Configuration Administrator and Auditor sessions exercise direct forbidden
  API calls and require `403`; the Auditor workspace has no form or button.
- The scenario uploads all six synthetic fixture files, observes real worker
  processing and the supported OCR extraction, corrects the reviewed field,
  and reaches deterministic validation through UI controls.
- Separate NGO Preparer, NGO Approver, and Government Reviewer sessions own
  correction, attestation/submission, and return/approval respectively.
- The v1 archive hash is captured before return and matched in the final audit
  projection. V2 is separately packaged, has a distinct hash, and its audit
  trail matches the captured v2 hash.
- Video, trace, JSON results, HTML report, runtime logs, Compose state, and
  screenshots for each role and material lifecycle checkpoint are retained.
- Headless CI and a paced headed mode share the same scenario. Headed mode
  defaults to `650 ms` slow motion and may be overridden for verification.

## Commands And Results

- `bash scripts/ci/run_static.sh`: 74 repository tests and 23 frontend tests
  passed; format, lint, type, ontology, ownership, architecture, SDLC, and
  production build gates passed.
- `bash scripts/ci/run_hermetic.sh tmp/evidence/SUB-26/hermetic`: two isolated
  fresh-volume runs passed, 189 API tests per pass, with identical fingerprint
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- `bash scripts/run_journey11.sh headless tmp/evidence/SUB-26/runner`: one clean
  Playwright test passed in 12.8 seconds (`expected=1`, `unexpected=0`,
  `flaky=0`). Retained trace SHA-256:
  `6c80df02f51f434381d023e6dc3b51596d854e51acfcb6cabdad6c7fec049f21`;
  video SHA-256:
  `feae52b0479a5b3d19c3cc263cbf5945d54ce550ddba233c0bc372fd40bb341e`.
- `JOURNEY11_SLOW_MO_MS=50 bash scripts/run_journey11.sh headed
  tmp/evidence/SUB-26/headed`: one headed test passed in 18.0 seconds. Retained
  trace SHA-256:
  `7f87d492e0062d4bc8b8b4ff1ebe1b6e23f02df181dff85b78bd15d7dcb3af70`;
  video SHA-256:
  `7faf127785191bec2664ec7472af0de71afb6afc0d0650eca117aae78dbdebc4`.

The draft-PR run produces the schema-valid machine evidence manifest against
the immutable base/head diff. Immutable AI review decisions are recorded only
after that manifest and hosted checks exist.

## Release Impact

Passing SUB-26 certifies the browser harness and unblocks SUB-55's final use of
it. SUB-53 still owns the operator-facing clean-run commands and SUB-55 still
owns the terminal clean-environment release decision and retained canonical
release artifacts.
