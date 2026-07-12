# SUB-66 Recovery Reconciliation Implementation Evidence

## Control

- Issue: SUB-66 / REC-12
- Branch: `codex/sub-66-recovery-recertification`
- Base SHA: `796f766fdaec7eedda4401b68537279f9bb9fa35`
- Project stage: Evidence Review
- Behavior change: no product runtime behavior; delivery certification and
  release-control evidence change
- Human code review: not required

## Generated Evidence

The eight applicable generation skills produced or updated:

- ADR/architecture: no-new-ADR rationale and current boundary decision in
  `docs/sdlc/recovery/SUB-66-recovery-certification.md`.
- Boundary: exact recovery merge matrix and ownership evidence mapping.
- Security/privacy: explicit public-repository disclosure exception plus
  retained synthetic/secret-scan controls.
- AI/config governance: current draft-only AI boundary, governed lifecycle, and
  narrow evaluation exception.
- Implementation/tests: fail-closed certification validator and eight focused
  negative tests.
- Requirements traceability: SUB-66 recovery row and continuation gate.
- Journey: clean Compose precursor and outstanding Journey 11 issue boundary.
- Release readiness: `Certified with exceptions`, effective only after review,
  merge, and post-merge verification.

## Machine Evidence

- Record: `docs/sdlc/recovery/SUB-66-recovery-certification.json`
- Validator: `scripts/check_recovery_certification.py`
- Tests: `scripts/tests/test_recovery_certification.py`
- Static integration: `scripts/ci/run_static.sh`
- Exact audit: 37 historical Done issues, including 24 invalidated provisional
  legacy approvals and 13 merged recovery/security issues.
- Prerequisite proof: ten SUB-66 blockers with full merge SHAs and post-merge
  verification flags; every SHA must be an ancestor of `origin/master`.
- Continuation proof: SUB-26, SUB-50, SUB-53, and SUB-55 fail closed as blocked
  until SUB-66 merge verification.

## Required Certification

Before immutable AI review:

1. Run `bash scripts/ci/run_static.sh` and retain exact policy/unit/frontend
   counts plus the production build.
2. Run `bash scripts/ci/run_hermetic.sh artifacts/ci-sub66` and retain both
   clean API logs, Compose states, equal semantic fingerprint, and hashes.
3. Build a schema-valid review manifest bound to the immutable base/head diff.
4. Open the draft PR and require the hosted `ContractView CI / certification`
   check.

Applicable immutable reviews are ADR/architecture, boundary, security/privacy,
AI/config governance, implementation/tests, requirements traceability,
Journey 11 certification, and release readiness. Any required fix becomes a new
commit and invalidates the prior review decision until re-reviewed.

Done requires the merge SHA on current `origin/master`, a second clean static
and two-pass Compose verification, attached completion manifest, Linear links
from affected Done issues, and only then dependency unblocking.

## Pre-Review Results

- Static gate: exit 0; 106 typed Python sources; 4 registries / 27 contracts;
  47 table owners / 174 named statements; 6 layers / 9 capability owners; 71
  repository policy/unit tests; 19 frontend tests; production build and web
  boundary check passed.
- Recovery validator: exit 0; exactly 37 Done issues and ten merged
  prerequisites.
- Clean runtime pass 1: exit 0; 180 API tests.
- Clean runtime pass 2: exit 0; 180 API tests.
- Equal reset fingerprint:
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- Retained SHA-256 values: API logs `4cafca817681aea9eb1aa5ab2d14653f5fa37b7efb54b9ba7467b977b2f61773`
  and `5371a6e0641ac4b44e85b93f30b64d9b23b559d4a161413d7562bf815a91af18`;
  Compose states `4cee4169675d863aa7f0ccf090a18f868d3e34351ed63575604491a455802dbd`
  and `cfce46ca02bdf16407f55e804834e46684e4f3e80651df4b0ef94e0a95f59a0a`.
- Public source check: GitHub reports visibility `PUBLIC`; current tracked-tree
  high-confidence pattern scan found no secret shapes outside scanner fixtures;
  GitHub's secret-scanning API reports the repository feature disabled. This is
  retained as EXC-02, not represented as a passing hosted security control.
