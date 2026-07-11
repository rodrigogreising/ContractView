# SUB-30 Implementation Evidence: Versioned POC Configuration

Status: Approved

## Scope

- One editable configuration draft per contract.
- Constrained contract covering service period, category limits, required evidence, five deterministic rule definitions and duplicate parameters, workflow labels, and package settings.
- Configuration Administrator authorization on draft updates and activation.
- Activation snapshots the validated draft into a new immutable, monotonically numbered configuration version.
- Invoice versions and validation runs hold database-enforced references to the exact configuration version used.

## Deterministic And Authority Boundaries

- Configuration validation is ordinary deterministic application code.
- AI cannot edit or activate configuration.
- Authorization executes before database mutation.
- A PostgreSQL trigger rejects updates and deletion of activated configuration snapshots.

## Verification

- Mutable draft and two distinct numbered activations.
- Version 1 remains unchanged after draft edits and version 2 activation.
- Direct SQL mutation of an activated version fails.
- NGO users cannot update or activate and create no version.
- Missing rule configuration fails validation.
- Invoice and validation foreign keys reject nonexistent configuration versions.
- Command: `docker compose run --rm api pytest -q`
- Result: 27 passed.

## Review

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Follow-up: SUB-38 exposes this constrained contract through the administrator UI; SUB-40 executes the versioned rules.
- Advancement: SUB-30 may move to Done while the project remains in Build.
