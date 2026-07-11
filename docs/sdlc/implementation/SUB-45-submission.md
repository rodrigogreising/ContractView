# SUB-45 Implementation Evidence: Immutable Submission

Status: Approved

## Scope

- Only the NGO Approver may submit the exact draft version.
- Submission requires its current attestation and generated package.
- One database transaction creates the append-only submission, government queue item, package-hash snapshot, submitted event, invoice state transition, and one-way artifact publication.
- Submitted invoice-line content is database-trigger locked; later correction must create a successor version.

## Verification

- Clean full API regression: `70 passed`.
- Frontend suite: `8 passed`; production build passed.
- Authority test proves preparer denial creates no submission.
- Invariant test verifies actor/role/time/version/configuration/hashes, queue creation, artifact publication, event linkage, and database rejection of submitted-line mutation.

## Review Decision

Approved. The server command enforces separation of duties and atomically publishes an immutable package/version to the government boundary.
