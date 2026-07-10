# Journey 09: AI-Assisted Extraction Requiring Human Correction

## Purpose

Prove that AI-assisted extraction can reduce manual work while preserving source evidence, model traceability, human correction, and deterministic validation boundaries.

## Actors

- Nonprofit fiscal staff.
- System actor: extraction pipeline.
- System actor: validation engine.
- System actor: provenance/event service.

## Preconditions

- Uploaded artifact requires OCR or AI-assisted extraction.
- AI-assisted extraction is enabled for the pilot context.
- Confidence threshold and review rules are configured.

## Workflow Path

1. Extraction pipeline classifies artifact and extracts draft fields.
2. System records source locations, confidence, model/prompt/parser version, and extraction plan.
3. Low-confidence or high-risk field is routed to human review.
4. Fiscal staff corrects the extracted value.
5. Correction is recorded as a lineage event.
6. Deterministic validation runs against corrected field and approved configuration.

## Expected Provenance Evidence

- Model, prompt, parser, and evaluation version.
- Source artifact and source location.
- Confidence score and review trigger.
- Human correction event with actor, timestamp, old value, new value, and reason where applicable.
- Validation run over corrected value.

## Failure Modes

- AI extraction cannot create approval, waiver, attestation, finalization, or blocking compliance result.
- Low-confidence field cannot silently proceed where review is required.
- Correction cannot overwrite original extraction history.
- Evaluation dataset updates must follow privacy and tenant-governance controls.

## Certification Criteria

- AI-derived field is traceable to source evidence and model metadata.
- Human correction is visible in field lineage.
- Validation decision is deterministic and based on corrected/current field value.
- No opaque AI output is required to explain a compliance-critical result.
