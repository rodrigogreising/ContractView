# Domain Types

## Purpose

This package defines the versioned shared domain primitives and closed lifecycle vocabulary for ContractView. `contract.json` is executable source input for the generated Python and TypeScript consumers.

Current contract version: `1.0.0`.

## Owned Responsibilities

- Define shared names and shapes for core ontology primitives.
- Define actor roles, invoice lifecycle states, issue statuses, severity categories, and human authority terms.
- Provide stable vocabulary for apps, services, events, rules, configuration, and fixtures.

## Explicit Non-Responsibilities

- Does not own runtime state.
- Does not implement workflow transitions.
- Does not execute validation rules.
- Does not perform persistence, API calls, or UI behavior.

## Owned Data Or Contracts

- `Artifact`, `Schema`, `Field`, `Entity`, `Relation`, `Rule`, `Workflow`, `View`, `Template`, `Event`, `ValidationRun`, and `ConfigurationBundle` vocabulary.
- Actor and role vocabulary.
- Invoice and issue lifecycle vocabulary.
- Version reference vocabulary.

## Allowed Dependencies

- No service internals.
- May depend on future language/runtime standard libraries only after a technology ADR.
- May be consumed by apps, services, and other shared packages.

## Events Emitted Or Consumed

- Defines event-related vocabulary but does not emit or consume events.

## Configuration Consumed Or Owned

- Defines configuration vocabulary but does not own configuration storage or lifecycle.

## Certification/Testing Setup

Current tests certify:

- Domain vocabulary matches ADR and architecture docs.
- Lifecycle states support certified journeys.
- Shared types do not encode stakeholder-specific invoice copies.
- Breaking changes are explicit and reviewed through architecture governance.

Run `python3 scripts/generate_shared_contracts.py --check` and
`python3 scripts/check_shared_contracts.py`. Optional fields may be added in a
minor version. Removals, required-field additions, type reinterpretation, and
closed-vocabulary changes require a major version and consumer migration.

## Related Certifiable Journeys

- All journey specs in [docs/journeys](../../docs/journeys/README.md).

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Human Authority Over Cross-Organizational Workflow.
