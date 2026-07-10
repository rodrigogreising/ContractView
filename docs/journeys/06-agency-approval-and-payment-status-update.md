# Journey 06: Agency Approval And Payment-Status Update

## Purpose

Prove that authorized agency users can approve reimbursement claims and that payment-status updates remain traceable after approval.

## Actors

- Agency finance reviewer.
- Agency supervisor or final approver.
- Nonprofit fiscal staff.
- System actor: API/workflow service.
- Optional system actor: integration job.

## Preconditions

- Invoice is submitted or resubmitted and ready for agency review.
- Required review levels are configured.
- Agency approver has authority for final approval.

## Workflow Path

1. Reviewer completes review and records approval recommendation or decision.
2. Supervisor/final approver completes required approval step where configured.
3. Workflow service changes invoice state to agency approved.
4. Payment status is updated manually or by integration.
5. Nonprofit sees approved and payment-status information.

## Expected Provenance Evidence

- Approval decision event with actor, role, timestamp, reason or approval note, and invoice version.
- Escalation or multi-level approval events where applicable.
- Payment-status event with source, timestamp, payment reference where available, and actor/integration job.
- Notification and reporting projection updates.

## Failure Modes

- Reviewer without final authority cannot create final approval.
- Payment execution failure does not roll back agency approval.
- Payment-status update cannot mutate approved invoice content.
- Integration job failure is retried or dead-lettered without corrupting invoice state.

## Certification Criteria

- Approval authority is human and permissioned.
- Approved status is distinct from submitted, screened, and paid.
- Payment status is traceable to a source and timestamp.
- Nonprofit and agency see the same canonical lifecycle state.
