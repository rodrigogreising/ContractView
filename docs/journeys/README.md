# Journey Certification Index

Journey certification proves that a given ContractView version can execute its job end to end across multiple users, organizations, system actors, and audit views.

Each journey must define:

- Actors.
- Preconditions.
- Workflow path.
- Expected provenance evidence.
- Failure modes.
- Certification criteria.

## Certification Rules

- A release is not certified unless all MVP-critical journeys pass.
- A journey passes only when user-visible behavior and provenance evidence are both correct.
- Journey certification must use explicit configuration versions and fixture data.
- Advisory AI or risk signals may help users prioritize work, but cannot create approval, waiver, attestation, finalization, or blocking compliance decisions.
- Submitted packages must remain immutable; corrections after submission require return, amendment, or resubmission.

## Initial Journey Set

| Journey | File | Primary purpose |
| --- | --- | --- |
| Nonprofit upload to draft invoice | [01-nonprofit-upload-to-draft-invoice.md](01-nonprofit-upload-to-draft-invoice.md) | Prove native data intake, artifact registration, extraction/import, and draft assembly. |
| Validation failure and issue resolution | [02-validation-failure-and-issue-resolution.md](02-validation-failure-and-issue-resolution.md) | Prove deterministic validation, issue workflow, correction lineage, and re-validation. |
| Nonprofit approval and submission | [03-nonprofit-approval-and-submission.md](03-nonprofit-approval-and-submission.md) | Prove human attestation, package generation, submission, and package lock. |
| Agency review and return | [04-agency-review-and-return.md](04-agency-review-and-return.md) | Prove agency review authority, evidence inspection, and structured return. |
| Resubmission after return | [05-resubmission-after-return.md](05-resubmission-after-return.md) | Prove amendment/resubmission semantics and preservation of original submission. |
| Agency approval and payment-status update | [06-agency-approval-and-payment-status-update.md](06-agency-approval-and-payment-status-update.md) | Prove approval authority and post-approval status tracking. |
| Auditor reconstruction of submitted claim | [07-auditor-reconstruction-of-submitted-claim.md](07-auditor-reconstruction-of-submitted-claim.md) | Prove inspectability and chain-of-custody reconstruction. |
| Support/admin configuration change with audit visibility | [08-support-admin-configuration-change.md](08-support-admin-configuration-change.md) | Prove configuration governance and support visibility controls. |
| AI-assisted extraction requiring human correction | [09-ai-assisted-extraction-human-correction.md](09-ai-assisted-extraction-human-correction.md) | Prove AI assistance remains traceable and human-reviewed. |
| Config/rule version change applied prospectively | [10-config-rule-version-change-prospectively.md](10-config-rule-version-change-prospectively.md) | Prove rule changes do not rewrite historical submissions. |

## Release Evidence

For each certified journey, release evidence should include:

- Version under test.
- Fixture contract, budget, artifacts, users, and configuration bundle.
- Executed path and timestamps.
- Validation run ids.
- Event ids or export references.
- Generated package hashes where applicable.
- Known exceptions and signoff.
