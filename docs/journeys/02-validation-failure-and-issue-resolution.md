# Journey 02: Validation Failure And Issue Resolution

## Purpose

Prove that deterministic validation flags defects, routes them for correction, and records correction lineage before re-validation.

## Actors

- Nonprofit fiscal staff.
- Nonprofit program/payroll collaborator.
- System actor: validation engine.
- System actor: API/workflow service.

## Preconditions

- Draft invoice exists with at least one validation defect.
- Active configuration bundle includes deterministic rules and issue workflow.
- Users have permissions for assigned issue categories.

## Workflow Path

1. Fiscal staff runs validation on the draft invoice.
2. Validation engine records rule inputs, outputs, severity, reason codes, and remediation guidance.
3. Workflow service creates or updates issues linked to affected invoice lines and validation results.
4. Assigned user corrects a field, uploads replacement evidence, excludes a line, or responds with structured information.
5. The affected lines are re-validated.
6. Full-package validation runs before final approval readiness.

## Expected Provenance Evidence

- Validation run id with invoice, artifact, budget, schema, mapping, rule, workflow, template, and parser/model versions.
- Issue events linked to invoice version, line item, validation result, and actor.
- Correction, replacement, exclusion, waiver, or accepted-risk events with rationale where required.
- Re-validation run ids and changed results.

## Failure Modes

- Invalid correction creates a new validation failure.
- Unauthorized user cannot waive or accept risk.
- Replacement document is registered as a new artifact version or related artifact, not a silent overwrite.
- Failed re-validation does not move invoice to ready-for-approval state.

## Certification Criteria

- Failed validation explains what failed, why, what evidence was used, and how to fix it.
- Issue resolution preserves source and correction history.
- Re-validation is stable for the same inputs and configuration versions.
- Waivers and accepted risks require authorized human actor, rationale, and audit visibility.
