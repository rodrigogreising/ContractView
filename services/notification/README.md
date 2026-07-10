# Notification Service

## Purpose

The notification service owns in-app/email notification delivery and future collaboration hooks for workflow events, issue assignments, returns, approvals, and operational alerts.

## Owned Responsibilities

- Deliver notifications for issue assignments, validation completion, submission receipts, returns, approvals, payment-status updates, support access requests, and configuration approvals.
- Track delivery attempts and notification state.
- Apply tenant and user notification preferences.
- Support future collaboration-channel integrations.

## Explicit Non-Responsibilities

- Does not create workflow transitions.
- Does not approve, waive, attest, return, or finalize invoices.
- Does not become the source of truth for invoice status.
- Does not expose sensitive evidence outside configured delivery policies.

## Owned Data Or Contracts

- Notification template contracts.
- Delivery attempt contracts.
- User notification state contracts.
- Collaboration hook contracts.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/event-contracts`.
- API/workflow read contracts.
- Provenance/event event subscriptions.
- Test fixtures for notification certification.

## Events Emitted Or Consumed

- Consumes workflow, issue, validation, submission, return, approval, payment-status, support access, and configuration lifecycle events.
- Emits notification queued, notification delivered, notification failed, and notification preference changed events.

## Configuration Consumed Or Owned

- Consumes notification templates, tenant delivery policy, user preferences, and data-minimization rules.
- Does not own workflow configuration.

## Certification/Testing Setup

Future tests must certify:

- Notifications are triggered for required workflow events.
- Delivery failure does not corrupt invoice state.
- Sensitive evidence is not sent where policy allows only references or summaries.
- Notifications preserve clear distinction between platform-screened, submitted, returned, approved, and paid statuses.
- Notification audit evidence is available when required by release certification.

## Related Certifiable Journeys

- [02 Validation failure and issue resolution](../../docs/journeys/02-validation-failure-and-issue-resolution.md)
- [04 Agency review and return](../../docs/journeys/04-agency-review-and-return.md)
- [06 Agency approval and payment-status update](../../docs/journeys/06-agency-approval-and-payment-status-update.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Human Authority Over Cross-Organizational Workflow.
