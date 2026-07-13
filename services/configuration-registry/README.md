# Configuration Registry

## Purpose

The configuration registry owns versioned reimbursement configuration: schemas, mappings, rules, workflows, views, templates, and configuration bundles.

## Owned Responsibilities

- Store versioned reimbursement configuration.
- Enforce lifecycle states: draft, tested, approved, active, superseded, retired.
- Record activation approvals, test evidence, affected contract scope, and activation time.
- Provide explicit configuration versions to validation, workflow, package generation, extraction, and views.
- Preserve historical configuration references for submitted invoices.
- Own immutable document profile versions, fixture/evaluation evidence, human
  approvals, lifecycle events, prospective active assignments, and draft
  cluster associations.

## Explicit Non-Responsibilities

- Does not own runtime invoice state.
- Does not hide customer-specific code behind configuration names.
- Does not activate AI-generated configuration without review, testing, approval, and versioning.
- Does not rewrite historical submitted invoice validation results.
- Does not execute validation rules.

## Owned Data Or Contracts

- Schema contracts.
- Mapping contracts.
- Rule definition metadata.
- Workflow, view, and template configuration contracts.
- Configuration bundle contracts and lifecycle events.
- Document profile definitions, fixture sets, evaluation evidence, exact
  profile references, and lifecycle contracts.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/configuration-contracts`.
- `packages/rule-contracts`.
- `packages/event-contracts`.
- Provenance/event API contracts.
- Test fixtures for configuration certification.

## Events Emitted Or Consumed

- Emits configuration drafted, tested, approved, activated, superseded, retired, and activation rejected events.
- Consumes test result evidence from validation and admin workflows.

## Configuration Consumed Or Owned

- Owns reimbursement configuration and its lifecycle.
- Consumes governance policy for who may approve and activate configuration.

## Certification/Testing Setup

Future tests must certify:

- Configuration cannot become active until tested and approved by an authorized actor.
- Production activation records owner, timestamp, affected scope, and test evidence.
- New configuration applies prospectively by default.
- Historical submitted invoices retain original configuration bundle versions.
- Existing draft invoices require explicit authorized re-validation when applying a new configuration.
- Profile activation requires exact id/version/hash, successful immutable
  fixture evidence, assigned-human approval, and prospective bundle activation.

## Related Certifiable Journeys

- [08 Support/admin configuration change with audit visibility](../../docs/journeys/08-support-admin-configuration-change.md)
- [10 Config/rule version change applied prospectively](../../docs/journeys/10-config-rule-version-change-prospectively.md)
- [02 Validation failure and issue resolution](../../docs/journeys/02-validation-failure-and-issue-resolution.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
- Human Authority Over Cross-Organizational Workflow.
