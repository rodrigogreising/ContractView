# Web App

## Purpose

The web app provides role-specific product workflows for nonprofit fiscal staff, nonprofit approvers, agency reviewers, auditors, support users, and customer admins over shared canonical invoice state.

## Owned Responsibilities

- Render nonprofit invoice preparation, issue resolution, approval, and submission workflows.
- Render agency review queue, evidence inspection, return, approval, and status workflows.
- Render auditor read-only reconstruction surfaces.
- Surface validation reason codes, source evidence, confidence, comments, package previews, and provenance summaries.
- Submit user commands to the API/workflow service.

## Explicit Non-Responsibilities

- Does not own canonical invoice state.
- Does not execute compliance-critical validation.
- Does not create approval, waiver, attestation, or finalization events without API/workflow authorization.
- Does not create stakeholder-specific invoice copies.
- Does not implement security or permission enforcement only in client logic.

## Owned Data Or Contracts

- UI route and view contracts.
- Role-specific view models derived from API contracts.
- Client-side presentation state.
- Accessibility and usability behavior for review workflows.

## Allowed Dependencies

- API contracts exposed by `services/api-workflow`.
- Shared domain types from `packages/domain-types`.
- Event and configuration display contracts where needed.
- Test fixtures from `packages/test-fixtures` for journey certification.

## Events Emitted Or Consumed

- Emits user commands through the API/workflow service.
- Consumes workflow state, validation results, issue status, artifact references, package previews, and provenance summaries.
- Does not emit material domain events directly.

## Configuration Consumed Or Owned

- Consumes role-specific view configuration.
- Consumes enabled feature flags and pilot rollout settings.
- Does not own production configuration lifecycle.

## Certification/Testing Setup

Future tests must certify:

- Role-specific screens render the same canonical invoice state with appropriate actions per role.
- Nonprofit upload-to-draft, issue resolution, approval/submission, agency review, return, resubmission, approval, and auditor reconstruction journeys can be executed through the UI.
- Submitted packages cannot be mutated through the UI.
- AI-derived fields show evidence, confidence, and correction path where applicable.
- Accessibility coverage includes keyboard-navigable review workflows and clear status language.

## Related Certifiable Journeys

- [01 Nonprofit upload to draft invoice](../../docs/journeys/01-nonprofit-upload-to-draft-invoice.md)
- [02 Validation failure and issue resolution](../../docs/journeys/02-validation-failure-and-issue-resolution.md)
- [03 Nonprofit approval and submission](../../docs/journeys/03-nonprofit-approval-and-submission.md)
- [04 Agency review and return](../../docs/journeys/04-agency-review-and-return.md)
- [07 Auditor reconstruction of submitted claim](../../docs/journeys/07-auditor-reconstruction-of-submitted-claim.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
- Human Authority Over Cross-Organizational Workflow.
