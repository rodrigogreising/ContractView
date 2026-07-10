# Journey 04: Agency Review And Return

## Purpose

Prove that agency reviewers can inspect evidence and return an invoice with structured reasons while preserving nonprofit submission history.

## Actors

- Agency finance reviewer.
- Agency supervisor when escalation is required.
- Nonprofit fiscal staff.
- System actor: API/workflow service.

## Preconditions

- Invoice has been submitted to agency.
- Agency reviewer has permission for the contract, queue, and review level.
- Submitted package and validation summary are locked.

## Workflow Path

1. Reviewer opens agency queue and selects submitted invoice.
2. Reviewer inspects summary, validation trace, source evidence, comments, and submitted package.
3. Reviewer identifies a defect requiring return.
4. Reviewer records structured return reason codes and optional clarification.
5. Workflow service changes invoice state to returned and notifies nonprofit.

## Expected Provenance Evidence

- Review access event where required by audit policy.
- Return decision event with actor, role, timestamp, reason codes, and invoice version.
- Notification event or delivery attempt.
- Link from returned issue to submitted package and affected evidence.

## Failure Modes

- Reviewer without authority cannot return invoice.
- Return cannot mutate original submitted package.
- Free-text-only return is insufficient when structured reason code is required.
- Bulk triage cannot convert platform-screened status into agency-approved status.

## Certification Criteria

- Returned invoice remains tied to original submitted version.
- Nonprofit receives structured return reasons.
- Agency return decision is visible to authorized auditors.
- Human actor authority is preserved and logged.
