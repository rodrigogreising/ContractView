# Journey 08: Support/Admin Configuration Change With Audit Visibility

## Purpose

Prove that customer or platform admins can change reimbursement configuration through governed lifecycle controls without silently altering historical submissions.

## Actors

- Implementation specialist.
- Customer admin.
- Platform support user.
- System actor: configuration registry.
- System actor: validation engine.

## Preconditions

- Active configuration bundle exists for pilot contract.
- Admin user has scoped permission for configuration changes.
- Historical submitted invoices exist.

## Workflow Path

1. Admin creates draft configuration change for schema, mapping, rule, workflow, view, or template.
2. Admin tests configuration against fixture or historical draft invoice data.
3. Authorized approver approves activation.
4. Configuration registry activates new bundle prospectively.
5. New draft invoices use new configuration.
6. Historical submitted invoices continue to display and reproduce prior configuration versions.

## Expected Provenance Evidence

- Draft configuration record.
- Test evidence and validation preview.
- Approval event with actor, timestamp, rationale, affected contracts, and activation time.
- Supersession relation from old bundle to new bundle.
- Support/admin access events where platform support participates.

## Failure Modes

- Unapproved draft configuration cannot run in production.
- AI-generated configuration cannot activate without review, testing, approval, and versioning.
- Support access must be time-limited, approved, and logged where required.
- Historical submitted invoices cannot be retroactively changed by new configuration.

## Certification Criteria

- Configuration lifecycle states are enforced.
- Activation is authorized, timestamped, and auditable.
- New configuration applies prospectively by default.
- Historical invoices remain reproducible using original configuration versions.
