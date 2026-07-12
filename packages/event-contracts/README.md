# Event Contracts

## Purpose

This package defines versioned material-event names, envelope requirements, actor references, version references, and chain-of-custody conventions in `contract.json`.

Current contract version: `1.0.0`; generated runtime vocabulary replaces the former duplicated Python event set.

## Owned Responsibilities

- Define material event naming conventions.
- Define required actor, organization, contract, invoice, artifact, and timestamp references.
- Define field lineage and artifact/version reference shapes.
- Define correction, amendment, waiver, accepted-risk, attestation, return, approval, and payment-status event contracts.

## Explicit Non-Responsibilities

- Does not store events.
- Does not decide event ordering or persistence technology.
- Does not mutate canonical workflow state.
- Does not replace provenance/event service behavior.

## Owned Data Or Contracts

- Event payload contracts.
- Actor and source references.
- Lineage reference contracts.
- Version reference contracts.
- Material action event categories.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/configuration-contracts` for configuration version references.
- No service internals.

## Events Emitted Or Consumed

- Defines event contracts.
- Does not emit or consume runtime events.

## Configuration Consumed Or Owned

- Defines how configuration versions are referenced from events.
- Does not own configuration lifecycle.

## Certification/Testing Setup

Current tests certify:

- Material events include actor, role, organization, contract, invoice, timestamp, and reason where applicable.
- Field lineage can link claimed amounts to source artifacts, source locations, validations, corrections, submitted packages, and decisions.
- Event contracts support audit reconstruction.
- Event contracts do not permit destructive overwrite semantics for material actions.

## Related Certifiable Journeys

- [03 Nonprofit approval and submission](../../docs/journeys/03-nonprofit-approval-and-submission.md)
- [04 Agency review and return](../../docs/journeys/04-agency-review-and-return.md)
- [06 Agency approval and payment-status update](../../docs/journeys/06-agency-approval-and-payment-status-update.md)
- [07 Auditor reconstruction of submitted claim](../../docs/journeys/07-auditor-reconstruction-of-submitted-claim.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Human Authority Over Cross-Organizational Workflow.
