# Journey 01: Nonprofit Upload To Draft Invoice

## Purpose

Prove that nonprofit fiscal staff can upload native reimbursement evidence and produce a draft invoice without manual package compilation.

## Actors

- Nonprofit fiscal staff.
- System actor: ingestion service.
- System actor: extraction pipeline.
- System actor: API/workflow service.

## Preconditions

- Pilot agency, nonprofit, contract, budget, and configuration bundle exist.
- Configuration bundle is active and includes ledger mapping, invoice schema, workflow, and template references.
- Nonprofit fiscal staff has permission to create draft invoices for the contract.

## Workflow Path

1. Fiscal staff starts a draft invoice for a reporting period.
2. Fiscal staff uploads ledger CSV/XLSX and supporting PDF/image artifacts.
3. Ingestion registers immutable artifacts, records hashes, and performs scan/deduplication checks.
4. Extraction/import captures structured rows and source locations.
5. Workflow service assembles draft invoice lines and links each material field to source evidence.
6. Fiscal staff sees draft totals, category totals, remaining budget, and unresolved import/extraction issues.

## Expected Provenance Evidence

- Artifact ids, versions, hashes, uploader, organization, and upload timestamp.
- Importer/parser/model versions for extracted or imported fields.
- Source row, cell, page, or bounding-box references for material fields.
- Mapping and schema versions.
- Draft invoice version and line-item relations.
- Events for upload, artifact registration, extraction/import completion, and draft assembly.

## Failure Modes

- Malware scan failure prevents artifact use.
- Duplicate artifact is flagged before creating duplicate claim lines.
- Extraction failure routes fields to manual review.
- Missing mapping prevents draft line creation and creates a visible issue.

## Certification Criteria

- Draft invoice is created from uploaded evidence.
- Every claimed amount in the draft traces to a source location or explicit manual entry event.
- Duplicate source data does not create duplicate claim lines.
- No submission, approval, waiver, or attestation event is created during this journey.
