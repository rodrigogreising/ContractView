# Package Generation Service

## Purpose

The package generation service deterministically creates agency-ready reimbursement packages from approved templates, invoice versions, validation summaries, and source evidence references.

## Owned Responsibilities

- Generate PDFs, CSVs, ZIP archives, package manifests, and validation summaries.
- Record generated artifact hashes and template versions.
- Produce reproducible package outputs for the same invoice, artifact, template, and configuration versions.
- Preserve original supporting documents while assembling review packages.

## Explicit Non-Responsibilities

- Does not fill missing compliance data with AI at generation time.
- Does not approve, waive, attest, return, or finalize invoices.
- Does not mutate submitted packages.
- Does not own source artifact registration.
- Does not own template activation lifecycle.

## Owned Data Or Contracts

- Package generation request contracts.
- Generated artifact and manifest contracts.
- Template input/output contracts.
- Package reproduction metadata.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/configuration-contracts`.
- `packages/event-contracts`.
- Artifact references from ingestion.
- Configuration registry read contracts.
- Provenance/event API contracts.
- Test fixtures for package certification.

## Events Emitted Or Consumed

- Consumes package generation requested commands.
- Emits package generated, package generation failed, and generated artifact registered events.

## Configuration Consumed Or Owned

- Consumes approved templates, schemas, views, and configuration bundle versions.
- Does not own production template approval or activation.

## Certification/Testing Setup

Future tests must certify:

- Generated packages are reproducible for the same recorded versions.
- Package manifests include source artifacts, generated artifacts, validation runs, and configuration versions.
- Failed package generation prevents submission.
- Submitted packages remain locked and immutable.
- Package artifacts are available for auditor reconstruction.

## Related Certifiable Journeys

- [03 Nonprofit approval and submission](../../docs/journeys/03-nonprofit-approval-and-submission.md)
- [05 Resubmission after return](../../docs/journeys/05-resubmission-after-return.md)
- [07 Auditor reconstruction of submitted claim](../../docs/journeys/07-auditor-reconstruction-of-submitted-claim.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
