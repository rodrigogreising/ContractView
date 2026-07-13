# Extraction Pipeline

## Purpose

The extraction pipeline converts uploaded artifacts into draft structured data while preserving source references, confidence, parser/model versions, and human correction lineage.

## Owned Responsibilities

- Run OCR, structured importers, parsers, and AI-assisted extraction where enabled.
- Produce draft fields with source locations and confidence.
- Record parser, importer, model, prompt, and extraction-plan versions.
- Route low-confidence or review-required fields to human review.
- Preserve original extraction and correction history.
- Compute versioned deterministic document fingerprints and noncanonical
  cluster projections.
- Match only exact active profile fingerprints and route changed/unknown input
  to `needs_profile_review` without canonical mutation.

## Explicit Non-Responsibilities

- Does not make compliance pass/fail decisions.
- Does not create approval, waiver, attestation, return, or finalization events.
- Does not overwrite corrected data destructively.
- Does not activate AI-generated configuration for production use.

## Owned Data Or Contracts

- Draft extraction output contracts.
- Source-location references: page, row, cell, bounding box, or section.
- Confidence and review-trigger contracts.
- Parser/model/prompt version contracts.
- `packages/extraction-contracts` route, fingerprint, match, cluster, ledger,
  source-location, and intake-result contracts.

## Allowed Dependencies

- `packages/domain-types`.
- `packages/configuration-contracts`.
- `packages/event-contracts`.
- `packages/extraction-contracts`.
- Artifact references from ingestion.
- Provenance/event API contracts.
- Test fixtures for extraction certification.

## Events Emitted Or Consumed

- Consumes artifact registered and import job created events.
- Emits extraction completed, extraction failed, low-confidence field routed, and correction captured events through the workflow/provenance boundaries.

## Configuration Consumed Or Owned

- Consumes schemas, mappings, extraction plans, review thresholds, and enabled AI policies.
- Does not own configuration lifecycle activation.

## Certification/Testing Setup

Future tests must certify:

- Every AI-derived field records source evidence, confidence, and model/prompt/parser version.
- Low-confidence fields route to human review when required.
- Human correction creates lineage without deleting original extraction history.
- Deterministic validation runs against reviewed/current field values, not opaque model output.
- Tenant privacy controls are respected for evaluation and future tuning datasets.
- English/Spanish closed fixtures reproduce exact fields/source locations and
  changed/unknown fixtures create no canonical expense or assignment.

For the current MVP, pinned local OCR is the only extraction adapter. Runtime
LLMs, hosted model calls, opaque classification, and automatic profile
assignment are prohibited by ADR 0003.

## Related Certifiable Journeys

- [01 Nonprofit upload to draft invoice](../../docs/journeys/01-nonprofit-upload-to-draft-invoice.md)
- [09 AI-assisted extraction requiring human correction](../../docs/journeys/09-ai-assisted-extraction-human-correction.md)
- [07 Auditor reconstruction of submitted claim](../../docs/journeys/07-auditor-reconstruction-of-submitted-claim.md)

## ADR Pillars Supported

- End-to-End Provenance.
- Configurable Reimbursement Ontology.
- Deterministic Execution, AI-Assisted Configuration.
