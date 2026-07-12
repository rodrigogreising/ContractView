# Rule Contracts

## Purpose

This package defines versioned executable contracts for deterministic validation rules, results, reason codes, and reproducible validation runs in `contract.json`.

Current contract version: `1.0.0`; it depends only on `domain-types` version references and vocabulary.

## Owned Responsibilities

- Define rule input and output interfaces.
- Define pass, fail, warning, and reviewer-note result categories.
- Define reason-code and remediation guidance conventions.
- Define deterministic execution expectations for validation engine implementations.

## Explicit Non-Responsibilities

- Does not execute rules.
- Does not store active rule configuration.
- Does not approve, waive, attest, or finalize invoices.
- Does not allow AI output to become an unreviewed blocking decision.

## Owned Data Or Contracts

- Rule input contracts.
- Rule output contracts.
- Severity taxonomy.
- Reason-code conventions.
- Validation result evidence references.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/configuration-contracts` for version references where needed.
- No service internals.

## Events Emitted Or Consumed

- Defines validation result payload shapes where needed.
- Does not emit or consume runtime events.

## Configuration Consumed Or Owned

- Defines rule contract shapes.
- Does not own configuration lifecycle or activation.

## Certification/Testing Setup

Current tests certify:

- Same rule inputs and configuration versions produce stable result shapes.
- Rule output contracts can carry evidence references and remediation guidance.
- Blocking errors, warnings, and reviewer-visible notes remain distinct.
- Advisory risk indicators cannot perform approval, waiver, attestation, finalization, or blocking behavior unless represented as explicit deterministic rules.

## Related Certifiable Journeys

- [02 Validation failure and issue resolution](../../docs/journeys/02-validation-failure-and-issue-resolution.md)
- [09 AI-assisted extraction requiring human correction](../../docs/journeys/09-ai-assisted-extraction-human-correction.md)
- [10 Config/rule version change applied prospectively](../../docs/journeys/10-config-rule-version-change-prospectively.md)

## ADR Pillars Supported

- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
- End-to-End Provenance.
