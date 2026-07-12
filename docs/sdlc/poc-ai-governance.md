# POC AI Governance

Status: Approved

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

The reimbursement configuration lifecycle is executable and separate from AI
evaluation: `draft -> tested -> approved -> active -> superseded -> retired`.
Deterministic tests create immutable evidence; an assigned human Configuration
Administrator alone approves and promotes a version. AI/system actors cannot
test, approve, activate, supersede, retire, or prepare rollback. Rollback creates
a new tested candidate and therefore cannot bypass evidence or human approval.
These controls govern the fixed POC reimbursement settings only and do not add
a customer-facing prompt/model editor.

## Implemented Versions

- Adapter contract: `OcrAdapter`.
- Provider: `tesseract-cli`.
- Model/runtime observed in the delivery image: `tesseract-5.5.0-eng` (recorded dynamically on every run).
- Prompt/instruction version: `vendor-invoice-fields-v1`.
- Parser version: `vendor-invoice-parser-v1`.
- Schema version: `vendor-date-amount-reference-v1`.
- Review threshold: 0.8500; all outputs require review regardless of confidence.
- Supported class: the synthetic EXP-003 vendor invoice, page 1.

These identifiers are explicit application configuration constants for the POC. A change is not considered approved until the golden evaluation below passes and this record is amended. Provider/model configuration remains a separately governed application delivery concern; the new reimbursement configuration UI cannot edit or promote the OCR adapter. Only one approved active POC adapter is delivered.

## Synthetic Evaluation Record

The clean containerized suite executes the real adapter on the immutable PDF fixture and requires:

- schema-valid vendor, date, proposed amount, and source reference: 4/4 fields;
- source page and immutable raw-response reference: present;
- provider/model/prompt/parser/schema identifiers: exact match;
- high-confidence result: still `needs_review`;
- intentionally wrong proposed amount: 1820.00, retained for human correction to 1280.00;
- low-confidence fixture adapter: routes to `LOW_CONFIDENCE` and creates proposed fields only;
- invalid response and provider outage: failed job/run, actionable error, zero proposed fields;
- authority actions or deterministic findings created by extraction: zero.

The golden set is intentionally narrow because this is an engineering POC, not evidence of broad document accuracy or business validation.

## SUB-64 Provenance Boundary

Immutable lineage plus invoice snapshots and version references retain the
extraction provider/model, prompt, parser, mapping, source location, and source
artifact hashes that contributed to downstream draft fields. AI output remains draft
evidence only: the typed relation graph can show support and derivation but
cannot create validation findings, attestations, submissions, returns, or
approvals. Those events require the canonical human actor and role, while
deterministic validation owns rule outcomes. Snapshot and lineage tests prove a
human correction appends a successor without rewriting the AI proposal or any
prior invoice version.

## Privacy And Tenant Data

- Only synthetic, non-branded fixtures are used.
- The active adapter runs locally in the Docker worker and sends no bytes to a third party.
- Source and raw response artifacts remain organization-scoped and hash-verifiable.
- Hosted providers, customer data, training reuse, and cross-tenant evaluation are out of scope.

## SUB-68 Reproducibility Boundary

Validation manifests record the exact extraction provider/model,
prompt/instruction, parser, and extraction-schema identifiers that contributed
draft inputs. These identifiers are evidence only. Deterministic validation
executes versioned shared rule contracts against a reviewed immutable invoice
snapshot; package generation executes a versioned template contract. Neither
path invokes AI, accepts an AI finding, or grants an AI/system actor lifecycle
authority.

Replay validates the retained extraction-component identifiers and hashes but
does not call a live model. A provider/model change therefore creates a new
traceable input manifest instead of silently changing a historical result.
The synthetic golden evaluation and separate configuration governance remain
required for any future adapter change.

## Review Result

- Decision: Approved.
- Findings: No blocking or required-fix findings.
- Evidence: focused real-adapter suite 3 passed; clean full API suite 53 passed; `docs/sdlc/implementation/SUB-35-ocr-extraction.md`.
- Required downstream control: satisfied by SUB-36. The UI shows source/confidence, requires explicit accept/correct, retains the proposal, and exposes only reviewed values to deterministic consumers.
- Release impact: AI gate remains satisfied only for the single synthetic supported class and Docker-local adapter documented here.
