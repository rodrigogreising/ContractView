# Journey 05: Resubmission After Return

## Purpose

Prove that nonprofit users can correct returned invoices and resubmit without losing the original submission chain.

## Actors

- Nonprofit fiscal staff.
- Nonprofit approver.
- Agency reviewer.
- System actor: validation engine.
- System actor: package generation service.

## Preconditions

- Invoice is in returned state.
- Return reason codes identify required corrections.
- Original submitted package remains locked.

## Workflow Path

1. Fiscal staff reviews return reasons and affected evidence.
2. Fiscal staff uploads replacement evidence, corrects fields, excludes lines, or adds structured response.
3. System creates amendment or resubmission version linked to original submission.
4. Validation engine re-runs deterministic checks using current applicable configuration.
5. Nonprofit approver attests to corrected package.
6. Package generation service creates resubmission package.
7. Workflow service submits resubmission to agency.

## Expected Provenance Evidence

- Return-to-correction relations.
- New artifact versions or related artifacts for replacement evidence.
- Correction events with actor and timestamp.
- Re-validation run ids.
- New attestation event and resubmission package hash.
- Relation from resubmission to original submitted package.

## Failure Modes

- Original package cannot be edited in place.
- Missing correction leaves return issue open.
- New validation failures block resubmission.
- Unauthorized approver cannot attest to resubmission.

## Certification Criteria

- Original and resubmitted packages are both inspectable.
- Resubmission history shows what changed, who changed it, and why.
- Agency sees resubmission as linked to prior return, not a disconnected invoice copy.
- Deterministic validation results are reproducible for the resubmission version.
