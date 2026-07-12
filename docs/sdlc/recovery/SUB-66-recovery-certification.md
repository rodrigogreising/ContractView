# SUB-66 Recovery Baseline Certification

Status: Candidate decision generated; immutable-diff AI review, merge, and clean
post-merge verification are still required before the decision takes effect.

## Decision

**Certified with exceptions** for return to the development `Build` stage after
SUB-66 is approved, merged, and post-merge verified. This is not Journey 11
completion, a POC release decision, or staging/production promotion.

The machine-readable controlling record is
`docs/sdlc/recovery/SUB-66-recovery-certification.json`. Its validator requires
exactly 37 historical Done issues, all ten merged recovery prerequisites,
explicit invalidation of provisional legacy approvals, owned exceptions, and a
fail-closed continuation gate.

## Architecture Decision

No new ADR is required. SUB-66 changes certification evidence, not the approved
runtime shape. ADR 0001's four pillars and ADR 0002's enforceable modular
monolith remain controlling. SUB-59 through SUB-65, SUB-67, and SUB-68 provide
the executable architecture, ownership, authorization, configuration,
provenance, reproducibility, web, and delivery controls being recertified.

## Historical Done Reconciliation

- All 37 Linear Done statuses are preserved.
- The 24 pre-recovery issues keep their historical status, but their original
  completion/approval claims are invalid as current certification evidence.
- Each pre-recovery issue is mapped to merged remediation issues and a durable
  repository evidence path in the machine record.
- The 13 recovery/security issues retain only the claim supported by their
  issue-scoped PR, immutable AI review policy, executable evidence, merge SHA,
  and clean post-merge proof.
- SUB-57 remains the one documented mixed legacy-baseline exception.
- SUB-58's fresh-context/human-review rule is replaced by SUB-69's immutable
  AI-review and executable-certification policy.
- SUB-79 remains valid for its allowlisted, history-free export only. It does
  not describe the durable repository that the owner subsequently made public.

## Merged Recovery Baseline

| Issue | PR | Merge SHA | Recovered control |
| --- | --- | --- | --- |
| SUB-58 | #2 | `08ae4ffef3f2ef386473149b596b6a5abbc147d8` | Isolated delivery and durable evidence |
| SUB-59 | #4 | `5894d61e9eafe176ec17459739ff3f1c10eeaa8c` | Enforceable modular-monolith architecture |
| SUB-60 | #5 | `8e7ad3644f847985833f3a524988b97451d391fe` | Canonical tenant authorization and auditor scope |
| SUB-61 | #6 | `1cc5d9a78060a0c40bb67cb8770d0c7de2f53639` | Executable ontology and generated contracts |
| SUB-62 | #7 | `be38a4a176dcca129bf053eebdc12dfc6d51be67` | Physical module and persistence ownership |
| SUB-63 | #8 | `a15d93637c0f998de5dc07374f6a6c975586f876` | Complete governed configuration lifecycle |
| SUB-64 | #9 | `45964570a986f7f87b772ba73d46b17c233c915e` | Versioned provenance and immutable snapshots |
| SUB-67 | #10 | `1a62ce922091a863863b2030a0f6773a87ecef1e` | Hermetic CI and durable machine manifests |
| SUB-68 | #12 | `7504ad34d7055d0977ddb5705ca1add43576a62c` | Reproducible validation and package bytes |
| SUB-65 | #13 | `796f766fdaec7eedda4401b68537279f9bb9fa35` | Feature-owned web modules and server contract context |

## Explicitly Invalidated Claims

The following claims may not be inferred from the historical Done states:

1. Done alone proves acceptance or release quality.
2. The legacy package/API layout enforced the ontology or module boundaries.
3. Legacy role filters proved canonical tenant authorization.
4. A mutable active configuration flag constituted governance.
5. Legacy events/packages were sufficient for exact reconstruction and replay.
6. Human or fresh-context review is universally required for code integration.
7. The SUB-79 history-free candidate describes the now-public durable repo.

The exact reasons and replacement evidence are machine checked in the JSON
record rather than left as prose-only qualification.

## Exception Register

| Exception | Owner | POC effect | Resolution boundary |
| --- | --- | --- | --- |
| Journey 11 final recording remains outstanding | SUB-26/SUB-50/SUB-53/SUB-55 | Blocks final POC certification | Complete SUB-55 in dependency order |
| Durable repository is public rather than the history-free candidate | Repository owner | Accepted disclosure exception; runtime controls unchanged | Use the allowlisted export or certify full-history disclosure before broader publication claims/licensing |
| Production identity, malware, retention, backup, DR, and penetration controls are deferred | Future production-readiness program | No effect on local synthetic POC | Required before hosted real-data use |
| GitHub official-action Node 20 runtime deprecation | CI maintenance | Non-blocking while required check passes | Update action/toolchain policy before compatibility removal |
| OCR evaluation covers one narrow synthetic document class | Future AI evaluation scope | Acceptable for Journey 11 fixture only | Expand evaluation before new classes or real data |

The public-repository exception is deliberate and bounded: the current tracked
tree contains no detected high-confidence secret shapes outside the scanner's
own negative fixtures, runtime fixtures use positive synthetic-data contracts,
and the owner explicitly changed visibility. The repository must not be
described as history-free, anonymous, or open source; its `LICENSE` remains
all-rights-reserved. GitHub's API reports repository secret scanning disabled;
enabling it is part of the exception's target resolution rather than a passing
control claimed by this certification.

## Continuation Gate

SUB-26, SUB-50, SUB-53, and SUB-55 remain blocked until all eight applicable
AI reviews approve the immutable SUB-66 PR diff, required CI passes, the PR is
merged, and the merge SHA passes a clean post-merge static and two-pass Compose
verification. Only then may the project return from `Evidence Review` to
`Build` and remove SUB-66 as their blocker.

Human code review is not required. Explicit human authority remains required
only for staging/production promotion and runtime human decisions.
