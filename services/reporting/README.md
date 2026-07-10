# Reporting Layer

## Purpose

The reporting layer provides operational read models, dashboards, exports, and analytics for invoice status, cycle time, open issues, bottlenecks, errors, cash-flow views, and audit support.

## Owned Responsibilities

- Build read models from canonical state, events, and approved metric definitions.
- Produce dashboards by agency, nonprofit, contract, period, amount, SLA, status, and issue category.
- Support exportable operational and audit reports.
- Track metric definitions and read-model versions.

## Explicit Non-Responsibilities

- Does not mutate canonical invoice state.
- Does not replace provenance records as certification evidence.
- Does not approve, waive, attest, return, or finalize invoices.
- Does not define compliance pass/fail semantics.

## Owned Data Or Contracts

- Reporting read-model contracts.
- Metric definition contracts.
- Dashboard and export contracts.
- Analytical replica contracts.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/event-contracts`.
- Provenance/event read contracts.
- API/workflow read contracts.
- Test fixtures for reporting certification.

## Events Emitted Or Consumed

- Consumes material workflow, validation, configuration, package, and payment-status events.
- Emits report generated and export generated events where audit policy requires.

## Configuration Consumed Or Owned

- Consumes metric definitions, role-specific report views, retention/export policies, and tenant scope.
- Does not own reimbursement workflow configuration.

## Certification/Testing Setup

Future tests must certify:

- Reports use consistent metric definitions.
- Dashboard projections do not contradict canonical state or provenance records.
- Exports respect tenant, role, retention, and privacy constraints.
- Reporting failure does not corrupt invoice workflow state.
- Audit exports include references back to source evidence and event records where required.

## Related Certifiable Journeys

- [06 Agency approval and payment-status update](../../docs/journeys/06-agency-approval-and-payment-status-update.md)
- [07 Auditor reconstruction of submitted claim](../../docs/journeys/07-auditor-reconstruction-of-submitted-claim.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Human Authority Over Cross-Organizational Workflow.
