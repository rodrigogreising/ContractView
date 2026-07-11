# SUB-44 Implementation Evidence: Immutable Invoice Package

Status: Approved

## Scope

- NGO Approver-only generation requires the current exact-version attestation.
- ReportLab renders a real invoice PDF using deterministic metadata.
- The package includes validation JSON, claim-level JSON/CSV manifest, supporting evidence bytes, and a deterministic ZIP.
- Claim entries link invoice/configuration/validation versions, ledger source coordinates, evidence, and extraction/correction status.
- PostgreSQL records every generated artifact and SHA-256; MinIO stores immutable bytes; append-only triggers protect package records.

## Verification

- Clean Compose reset and complete API regression: `69 passed`.
- Frontend component suite: `8 passed`; production TypeScript/Vite build passed.
- Integrity test opens the ZIP, verifies every manifest hash, confirms five evidence members and `%PDF` bytes, and checks the package event/hash records.
- Preparer generation is rejected before mutation.
- Rendered PDF inspected at `tmp/pdfs/sub-44-invoice-1.png`: no clipping, overlap, broken glyphs, or unreadable fields.

## Review Decision

Approved. The package is generated from a human-attested immutable input set, records durable hashes and provenance, and contains no runtime-AI authority or non-synthetic data.
