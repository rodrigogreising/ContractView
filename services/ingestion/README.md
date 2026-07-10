# Ingestion Service

## Purpose

The ingestion service owns upload intake, artifact registration, malware scan orchestration, deduplication, checksum validation, and import job creation.

## Owned Responsibilities

- Register uploaded artifacts with immutable references and hashes.
- Record uploader, tenant, organization, contract context, and upload timestamp.
- Coordinate malware scanning and deduplication.
- Create structured import jobs for CSV/XLSX and similar source files.
- Provide artifact references to downstream extraction, validation, package, and provenance flows.

## Explicit Non-Responsibilities

- Does not decide whether a claim is reimbursable.
- Does not approve, return, waive, attest, or finalize invoices.
- Does not mutate artifact bytes after registration.
- Does not own field extraction confidence or parser/model execution records.

## Owned Data Or Contracts

- Artifact registration contracts.
- Upload batch metadata.
- Scan and deduplication result contracts.
- Import job initiation contracts.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/event-contracts`.
- Object storage abstractions selected by future ADR.
- Provenance/event API contracts.
- Test fixtures for upload and import certification.

## Events Emitted Or Consumed

- Emits artifact uploaded, artifact registered, scan completed, duplicate detected, and import job created events.
- Consumes upload commands from API/workflow service.

## Configuration Consumed Or Owned

- Consumes allowed file type, tenant retention, scan, and import configuration.
- Does not own reimbursement schemas, mappings, or rules.

## Certification/Testing Setup

Future tests must certify:

- Uploaded artifacts are immutable and hash-verifiable.
- Malware scan failure prevents artifact use in claim lines.
- Duplicate artifacts are detected before duplicate claim lines are created.
- Failed upload/import jobs do not corrupt invoice state.
- Upload evidence is available for journey and release certification.

## Related Certifiable Journeys

- [01 Nonprofit upload to draft invoice](../../docs/journeys/01-nonprofit-upload-to-draft-invoice.md)
- [05 Resubmission after return](../../docs/journeys/05-resubmission-after-return.md)
- [07 Auditor reconstruction of submitted claim](../../docs/journeys/07-auditor-reconstruction-of-submitted-claim.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
