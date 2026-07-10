# Journey 10: Config/Rule Version Change Applied Prospectively

## Purpose

Prove that rule and configuration changes apply prospectively by default and do not rewrite historical validation or submission records.

## Actors

- Rule author.
- Customer admin or authorized approver.
- Nonprofit fiscal staff.
- Agency reviewer.
- System actor: configuration registry.
- System actor: validation engine.

## Preconditions

- Active configuration bundle has been used to submit at least one invoice.
- A draft invoice exists or can be created after the change.
- Rule author has permission to create draft rule/configuration changes.

## Workflow Path

1. Rule author drafts a rule or mapping change.
2. Rule author tests the change against fixtures or historical draft data.
3. Authorized approver activates new configuration bundle.
4. New draft invoice validates against the new configuration version.
5. Previously submitted invoice continues to show original configuration and validation run.
6. If authorized admin re-runs validation for an existing draft invoice, the new validation run records the new configuration version.

## Expected Provenance Evidence

- Prior and new configuration bundle versions.
- Test evidence for changed rule or configuration.
- Activation approval event.
- Validation runs before and after change with exact versions.
- Historical invoice references to original bundle.

## Failure Modes

- Production activation without approval is blocked.
- Historical submitted invoices are not recalculated in place.
- Existing draft invoices require explicit authorized re-validation to use new configuration.
- Rule false-positive/false-negative metrics can be tracked without changing historical results.

## Certification Criteria

- New configuration applies prospectively by default.
- Historical submitted invoice remains reproducible.
- Re-validation creates a new validation run rather than overwriting prior result.
- Users can see which configuration version was used for each invoice or validation result.
