# SUB-35 Implementation Evidence: Real OCR Draft Extraction

Status: Approved

## Real Adapter

- `TesseractCliAdapter` is a replaceable `OcrAdapter` implementation.
- The Docker worker renders page 1 with Poppler and invokes Tesseract 5 English OCR against the actual synthetic EXP-003 PDF.
- No extraction field or final state is seeded.

## Trace

- Source and immutable raw OCR response artifacts are linked by `derived_from`.
- Each run records provider, model, prompt, parser, schema, page, confidence, routing status, and error if applicable.
- The model identifier includes the actual Tesseract runtime version and English language pack observed by the worker.
- Draft fields record vendor, date, amount, source reference, confidence, page, and proposed review state.
- Field lineage and `extraction_drafted`/`extraction_failed` events are append-only.

## AI/OCR Authority

- Every successful output is `needs_review`; even high-confidence fields remain proposed.
- Confidence below 0.8500 routes to `LOW_CONFIDENCE` review.
- Provider failure or invalid schema creates a visible failed run/job and zero fields.
- OCR creates no deterministic finding, attestation, submission, return, or approval.

## Golden Expectation

- Vendor: Northstar Learning Supply.
- Date: 2026-06-18.
- Proposed amount: 1820.00 (intentionally requires correction to the approved claim total 1280.00 in SUB-36).
- Source reference: VENDOR-INVOICE-EXP-003.

## Verification And Review

- Focused real-adapter/governance suite: 3 passed.
- Authoritative clean full API suite: 53 passed.
- Implementation review decision: Approved; no blocking or required-fix findings.
- AI-governance review decision: Approved; no runtime validation or human-authority action is produced, every output remains proposed, and failure paths create zero fields.
- Follow-up: SUB-36 supplies the required visible human accept/correct path and consumes the intentionally wrong proposal.
