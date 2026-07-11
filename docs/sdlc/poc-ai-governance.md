# POC AI Governance

Status: Approved with implementation evidence required

## Intended Use

Use one real, replaceable OCR/LLM adapter to extract draft vendor, date, amount, and evidence-reference fields from one supported synthetic receipt/vendor-invoice format.

## Prohibited Authority

AI cannot:

- Decide submission blockers, warnings, budgets, totals, or duplicates.
- Attest, submit, return, approve, waive, or finalize.
- Change active configuration.
- Overwrite a human correction or historical value.

## Required Trace

Each extraction records artifact/version, page or region, provider/model, prompt/parser version, raw structured response reference, normalized draft value, confidence, timestamp, and later human correction.

## Fixture Evaluation

- Maintain a small synthetic golden set for the single supported document class.
- Assert expected fields, source references, schema validity, and low-confidence routing.
- Include one intentionally ambiguous or incorrect value that the NGO Preparer corrects in the canonical journey.
- Treat provider outage and invalid response as visible processing failure with retry/manual correction; never invent a value.

## Human Review

All extracted fields are visibly marked as proposed until accepted or corrected. Validation consumes the current reviewed value and explicit extraction/correction history.

## Configuration Governance

Prompt, parser, extraction schema, and provider/model identifier are versioned application configuration. Changing them requires fixture evaluation evidence, but the POC does not implement a customer-facing AI configuration editor.
