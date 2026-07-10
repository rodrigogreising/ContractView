# Validation Engine

## Purpose

The validation engine executes deterministic reimbursement rules over explicit invoice, artifact, budget, schema, mapping, workflow, template, and configuration versions.

## Owned Responsibilities

- Execute deterministic validation rules.
- Record validation runs with exact inputs and configuration versions.
- Produce pass, fail, warning, and reviewer-note results with reason codes.
- Explain what failed, why it failed, what evidence was used, and how to fix it.
- Support stable re-runs for identical inputs and configuration versions.

## Explicit Non-Responsibilities

- Does not use AI output as an unreviewed blocking decision.
- Does not query non-versioned mutable UI state during validation.
- Does not approve, waive, attest, return, or finalize invoices.
- Does not own configuration activation.
- Does not mutate invoice state directly.

## Owned Data Or Contracts

- Validation run contracts.
- Rule input/output contracts.
- Severity and reason-code contracts.
- Validation summary contracts.
- Deterministic execution contract.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/rule-contracts`.
- `packages/configuration-contracts`.
- `packages/event-contracts`.
- Configuration registry read contracts.
- Provenance/event API contracts.
- Test fixtures for deterministic rule certification.

## Events Emitted Or Consumed

- Consumes validation requested commands with explicit version references.
- Emits validation run completed, validation run failed, and validation result events.

## Configuration Consumed Or Owned

- Consumes active or explicitly selected schemas, mappings, rules, workflows, templates, budgets, and configuration bundles.
- Does not own draft/tested/approved/active lifecycle transitions.

## Certification/Testing Setup

Future tests must certify:

- Same inputs plus same configuration versions produce same outputs.
- Rule results include reason codes, evidence references, and remediation guidance.
- Blocking errors, warnings, and reviewer-visible notes are separated.
- Historical validation runs remain reproducible.
- Advisory risk indicators cannot approve, waive, attest, finalize, or block submission unless implemented as explicit deterministic rules.

## Related Certifiable Journeys

- [02 Validation failure and issue resolution](../../docs/journeys/02-validation-failure-and-issue-resolution.md)
- [05 Resubmission after return](../../docs/journeys/05-resubmission-after-return.md)
- [09 AI-assisted extraction requiring human correction](../../docs/journeys/09-ai-assisted-extraction-human-correction.md)
- [10 Config/rule version change applied prospectively](../../docs/journeys/10-config-rule-version-change-prospectively.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
