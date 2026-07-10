# Admin Console

## Purpose

The admin console supports customer onboarding, contract setup, configuration lifecycle management, support access controls, rule testing, and rollout operations.

## Owned Responsibilities

- Provide interfaces for contract, budget, schema, mapping, rule, workflow, view, and template configuration.
- Support configuration lifecycle transitions: draft, tested, approved, active, superseded, retired.
- Display rule test results, validation previews, activation records, and affected contract scope.
- Manage support access workflows with approval, time bounds, and audit visibility.
- Support pilot feature flags and rollout controls.

## Explicit Non-Responsibilities

- Does not bypass configuration registry approval rules.
- Does not activate untested or unapproved production configuration.
- Does not mutate historical submitted invoices when configuration changes.
- Does not grant support access without configured approval and logging controls.
- Does not hide customer-specific code behind configuration names.

## Owned Data Or Contracts

- Admin view models and workflows.
- Configuration authoring UI contracts.
- Rule test and validation preview presentation contracts.
- Support access request and approval UI contracts.

## Allowed Dependencies

- API/workflow commands for admin and support actions.
- Configuration registry contracts.
- Rule contracts and domain types.
- Test fixtures for configuration certification.

## Events Emitted Or Consumed

- Emits admin commands through API/workflow and configuration registry boundaries.
- Consumes configuration lifecycle events, rule test results, support access events, and activation records.
- Does not directly write material provenance events.

## Configuration Consumed Or Owned

- Consumes and edits draft configuration through configuration registry APIs.
- Does not own active configuration storage or lifecycle enforcement.

## Certification/Testing Setup

Future tests must certify:

- Configuration cannot become active until tested and approved by an authorized actor.
- AI-generated configuration remains draft until reviewed, tested, approved, and versioned.
- Historical submitted invoices retain original configuration versions after activation of new configuration.
- Support access is time-limited, approved, and logged.
- Configuration changes are visible in release certification evidence.

## Related Certifiable Journeys

- [08 Support/admin configuration change with audit visibility](../../docs/journeys/08-support-admin-configuration-change.md)
- [10 Config/rule version change applied prospectively](../../docs/journeys/10-config-rule-version-change-prospectively.md)
- [09 AI-assisted extraction requiring human correction](../../docs/journeys/09-ai-assisted-extraction-human-correction.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
- Human Authority Over Cross-Organizational Workflow.
