# API/Workflow Service

## Purpose

The API/workflow service is the command boundary for user-facing workflow, permissions, invoice lifecycle, issue handling, submission, agency review, and human authority events.

## Owned Responsibilities

- Own canonical invoice lifecycle state.
- Enforce role-based permissions for material workflow commands.
- Coordinate ingestion, validation, package generation, submission, return, approval, amendment, and payment-status commands.
- Own issue workflow and assignment state.
- Emit material workflow events through the provenance/event boundary.

## Explicit Non-Responsibilities

- Does not own artifact storage internals.
- Does not execute validation rule internals.
- Does not treat reporting projections as canonical state.
- Does not bypass human authority for attestations, waivers, returns, approvals, or finalization.
- Does not silently mutate submitted packages.

## Owned Data Or Contracts

- Invoice lifecycle state.
- Workflow command contracts.
- Permission decision contracts.
- Issue state and assignment contracts.
- Submission, return, approval, amendment, and payment-status command contracts.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/event-contracts`.
- `packages/configuration-contracts`.
- Validation engine API contracts.
- Provenance/event API contracts.
- Package generation API contracts.
- Test fixtures for certified journeys.

## Events Emitted Or Consumed

- Emits workflow transition, permission decision, issue, attestation, waiver, accepted-risk, submission, return, approval, amendment, and payment-status events.
- Consumes validation results, package manifests, artifact references, and configuration bundle versions.

## Configuration Consumed Or Owned

- Consumes workflow, view, rule severity, and configuration bundle versions.
- Does not own configuration lifecycle storage.

## Certification/Testing Setup

Future tests must certify:

- Permissioned state transitions for every material invoice lifecycle change.
- Human actor requirements for attestation, waiver, accepted risk, return, approval, escalation, and finalization.
- Nonprofit and agency views observe the same canonical invoice state.
- Post-submission changes create amendment, return, or resubmission flows.
- Failed integration or package generation does not corrupt invoice state.

## Related Certifiable Journeys

- [02 Validation failure and issue resolution](../../docs/journeys/02-validation-failure-and-issue-resolution.md)
- [03 Nonprofit approval and submission](../../docs/journeys/03-nonprofit-approval-and-submission.md)
- [04 Agency review and return](../../docs/journeys/04-agency-review-and-return.md)
- [05 Resubmission after return](../../docs/journeys/05-resubmission-after-return.md)
- [06 Agency approval and payment-status update](../../docs/journeys/06-agency-approval-and-payment-status-update.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
- Human Authority Over Cross-Organizational Workflow.
