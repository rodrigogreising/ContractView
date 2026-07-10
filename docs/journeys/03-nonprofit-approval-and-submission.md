# Journey 03: Nonprofit Approval And Submission

## Purpose

Prove that an authorized nonprofit actor can attest to and submit an agency-ready package, and that submitted content is locked.

## Actors

- Nonprofit fiscal staff.
- Nonprofit approver or executive.
- System actor: package generation service.
- System actor: API/workflow service.

## Preconditions

- Invoice has passed required deterministic validation or has authorized waivers/accepted risks.
- Generated package preview is available.
- Nonprofit approver has attestation permission.

## Workflow Path

1. Fiscal staff prepares invoice for final approval.
2. Approver reviews totals, warnings, validation summary, source evidence, and package preview.
3. Approver completes attestation or e-signature.
4. Package generation service creates final package and manifest from approved template/configuration versions.
5. Workflow service submits package through configured channel or marks it ready for manual submission.
6. Invoice state changes to submitted to agency.

## Expected Provenance Evidence

- Human attestation event with actor, role, timestamp, invoice version, and rationale/attestation text.
- Generated package artifact id, hash, template version, and manifest.
- Validation summary and validation run references.
- Submission event, channel, receipt, and submitted package reference.

## Failure Modes

- Unauthorized actor cannot attest.
- Unresolved blocking validation failure prevents submission.
- Package generation failure prevents submission.
- Any post-submission change creates amendment/resubmission workflow instead of mutating submitted content.

## Certification Criteria

- Submitted package is immutable and reproducible from recorded versions.
- Nonprofit and agency views show the same canonical submitted invoice state.
- Attestation is recorded against the exact submitted invoice version.
- Platform-screened status is not represented as agency approval.
