# Configuration Contracts

## Purpose

This package defines shared executable contracts for rules, workflows, views,
templates, configuration bundles, extraction-component references, validation
input manifests, package build inputs, package reproduction manifests, and
exact schema/mapping version references in `contract.json`.

Current contract version: `1.1.0`. The contract defines the full lifecycle but
does not activate configuration; REC-06 implements its commands and
persistence. REC-09 uses the versioned contracts for runtime reproduction.

## Owned Responsibilities

- Define configuration bundle shape and version references.
- Define lifecycle state vocabulary: draft, tested, approved, active, superseded, retired.
- Define schema/mapping reference, workflow, view, and template contract vocabulary.
- Define activation evidence and supersession reference shapes.
- Define immutable validation/package reproduction input and output shapes.

## Explicit Non-Responsibilities

- Does not store configuration.
- Does not activate production configuration.
- Does not execute validation rules.
- Does not hide customer-specific code paths behind configuration contracts.
- Does not mutate historical invoice records.

## Owned Data Or Contracts

- Schema and mapping version-reference vocabulary; REC-06 owns their complete definitions.
- Workflow, view, and template contract vocabulary.
- Configuration bundle and lifecycle contracts.
- Extraction component, validation input, package build, file digest, and
  package reproduction contracts.
- Activation approval and test evidence references.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/rule-contracts` for rule contract references.
- No service internals.

## Events Emitted Or Consumed

- Defines configuration event payload shapes where needed.
- Does not emit or consume runtime events.

## Configuration Consumed Or Owned

- Defines configuration contracts.
- Does not own configuration lifecycle enforcement.

## Certification/Testing Setup

Current tests certify:

- Configuration contracts support draft, tested, approved, active, superseded, and retired states.
- Submitted invoices can reference exact configuration bundle versions.
- Historical configuration references remain valid after supersession.
- AI-generated configuration can be represented as draft but not active without approval evidence.

## Related Certifiable Journeys

- [08 Support/admin configuration change with audit visibility](../../docs/journeys/08-support-admin-configuration-change.md)
- [10 Config/rule version change applied prospectively](../../docs/journeys/10-config-rule-version-change-prospectively.md)

## ADR Pillars Supported

- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
- End-to-End Provenance.
