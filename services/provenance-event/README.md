# Provenance/Event Service

## Purpose

The provenance/event service records append-only material events, field lineage, artifact/version references, validation evidence, and reconstruction data.

## Owned Responsibilities

- Store append-only material events.
- Link invoice fields to source artifacts, source locations, parsers, mappings, validations, corrections, submissions, returns, approvals, and payment updates.
- Support audit reconstruction and evidence export.
- Preserve chain of custody from upload to submission to approval.
- Represent corrections and amendments as new events rather than destructive edits.

## Explicit Non-Responsibilities

- Does not replace canonical workflow state.
- Does not become only application logs.
- Does not allow event mutation without explicit correction/amendment semantics.
- Does not grant mutation rights to auditors.
- Does not make compliance pass/fail decisions.

## Owned Data Or Contracts

- Event stream contracts.
- Field lineage contracts.
- Artifact/version reference contracts.
- Reconstruction query/export contracts.
- Chain-of-custody evidence contracts.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/event-contracts`.
- `packages/configuration-contracts`.
- Test fixtures for audit reconstruction.

## Events Emitted Or Consumed

- Consumes material events from workflow, ingestion, extraction, validation, package generation, configuration, reporting, notification, and integration surfaces.
- Emits read/query/export responses, not material workflow decisions.

## Configuration Consumed Or Owned

- Consumes retention, legal hold, redaction, and export policy configuration.
- Does not own reimbursement rule or workflow configuration lifecycle.

## Certification/Testing Setup

Future tests must certify:

- Claimed amounts can be reconstructed from source artifact to field, validation, correction, submitted package, return, approval, and payment status.
- Append-only event behavior preserves prior values and corrections.
- Retention/deletion policies preserve required audit evidence through legal holds, tombstones, hashes, or redacted lineage.
- Auditors have inspectability without mutation rights.
- Queryable projections do not contradict provenance records.

## Related Certifiable Journeys

- [07 Auditor reconstruction of submitted claim](../../docs/journeys/07-auditor-reconstruction-of-submitted-claim.md)
- [03 Nonprofit approval and submission](../../docs/journeys/03-nonprofit-approval-and-submission.md)
- [04 Agency review and return](../../docs/journeys/04-agency-review-and-return.md)
- [06 Agency approval and payment-status update](../../docs/journeys/06-agency-approval-and-payment-status-update.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Human Authority Over Cross-Organizational Workflow.
