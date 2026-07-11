# Test Fixtures

The POC fixture pack is synthetic, deterministic, and non-branded.

- `scenario.json` is the machine-readable source of truth for organizations, personas, contract, budget, draft configuration, expected validation, return feedback, and final state.
- `expected.json` contains compact assertions for unit, integration, and Playwright tests.
- `files/ledger-june-2026.csv` and the matching XLSX workbook contain the same five source expenses.
- Supporting PDF/image artifacts are intentionally synthetic. EXP-003 contains a printed subtotal and an approved adjusted total so the demo preserves an AI proposal followed by human correction.

Seed/reset loads initial actors and configuration only. It never seeds invoice processing, submission, return, resubmission, or approval state.

## Purpose

This package will own certified fixture data for journey certification, deterministic validation tests, provenance reconstruction tests, configuration lifecycle tests, and release evidence.

## Owned Responsibilities

- Provide sample agencies, nonprofits, contracts, budgets, users, roles, ledgers, artifacts, rules, schemas, mappings, workflows, templates, and configuration bundles.
- Provide journey fixture sets for release certification.
- Provide known-good and known-failing examples for validation, extraction, package generation, provenance, and configuration tests.
- Preserve fixture version history when certification expectations change.

## Explicit Non-Responsibilities

- Does not implement application behavior.
- Does not store production customer data.
- Does not include sensitive real data unless explicitly approved, redacted, and governed.
- Does not replace release evidence from actual certified runs.

## Owned Data Or Contracts

- Fixture catalog contracts.
- Synthetic artifact references.
- Sample configuration bundle references.
- Expected validation result references.
- Journey certification fixture descriptions.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/rule-contracts`.
- `packages/event-contracts`.
- `packages/configuration-contracts`.
- No service internals.

## Events Emitted Or Consumed

- May define expected event sequences for certification tests.
- Does not emit or consume runtime events.

## Configuration Consumed Or Owned

- Owns sample configuration bundles for tests.
- Does not own production configuration.

## Certification/Testing Setup

Future tests must certify:

- Fixtures cover MVP-critical journeys.
- Fixture data supports deterministic validation re-runs.
- Fixture artifacts and expected lineage support audit reconstruction tests.
- Fixture configuration covers draft/tested/approved/active/superseded/retired lifecycle scenarios.
- Fixture data is synthetic or governed according to privacy requirements.

## Related Certifiable Journeys

- All journey specs in [docs/journeys](../../docs/journeys/README.md).

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
- Human Authority Over Cross-Organizational Workflow.
