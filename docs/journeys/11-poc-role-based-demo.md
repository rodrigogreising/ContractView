# Journey 11: Role-Based POC Demo From Configuration To Approval

## Purpose

Certify the complete ContractView POC through one visible, recorded browser journey using synthetic data, real authentication, real processing, deterministic validation, immutable versions, and human authority.

## Actors

- Configuration Administrator.
- NGO Preparer.
- NGO Approver.
- Government Reviewer.
- Auditor.
- Background worker and deterministic validation system actors.

## Preconditions

- Docker Compose environment starts cleanly.
- Synthetic users, organizations, contract, budget, ledger, and evidence fixtures are available.
- OCR/LLM adapter credentials or an explicitly configured real compatible provider are available.
- No active reimbursement configuration exists before the journey begins.

## Workflow Path

1. Administrator authenticates, saves a bounded draft, runs deterministic
   configuration tests, records human approval, and prospectively activates
   immutable configuration version 1.
2. Preparer authenticates, uploads ledger and evidence, and observes real processing.
3. Preparer corrects one extracted value and resolves deterministic findings.
4. Approver authenticates, attests, generates package version 1, and submits it.
5. Reviewer authenticates and returns version 1 with structured feedback.
6. Preparer authenticates and creates a linked corrected revision.
7. Approver authenticates, re-attests, generates package version 2, and resubmits it.
8. Reviewer authenticates and approves version 2.
9. Auditor authenticates and reconstructs both versions and their decision history.

## Expected Provenance Evidence

- Authentication session and logout events for each persona.
- Configuration definition, immutable test evidence, human approval, lifecycle
  event hashes, rationale, and activation event.
- Original artifact hashes, upload actor, and source locations.
- Importer, OCR/LLM, prompt/parser, confidence, and correction records.
- Invoice versions, mappings, rule versions, validation runs, findings, and resolutions.
- Attestation actors and exact invoice/package versions.
- Package manifests and distinct hashes for versions 1 and 2.
- Return feedback, revision relation, resubmission, approval, and audit-query evidence.
- Versioned event envelopes with canonical actor role/organization, resource
  organization, reason, schema, immutable references, and event hashes.
- Validation, attestation, package, and submission snapshots for both invoice
  versions plus typed support/derivation/mapping/validation/submission/return/
  amendment/approval relations.
- A same-field correction chain from the immutable v1 mapping through the v2
  clone to the corrected v2 value.

## Failure Modes

- Persona can access an unauthorized action or direct API command.
- Logout leaves the prior session usable.
- Processing is bypassed through seeded final-state records.
- Configuration activation bypasses testing or human approval, mutates an old
  version, or permits an AI/system actor to govern the lifecycle.
- AI output creates a blocking compliance result or authority event.
- A blocker does not prevent NGO approval/submission.
- Return edits version 1 instead of creating a linked revision.
- Version 1 changes after version 2 is created.
- A material event lacks actor/version context, a relation crosses an invisible
  tenant boundary, or an invoice snapshot/validation result can be mutated.
- Expense-date lineage points to a claimed-amount predecessor or a v2 correction
  skips the cloned same-field predecessor.
- Auditor cannot reconstruct the claimed amount and both packages.
- Playwright requires manual database changes or test-only role switching.

## Certification Criteria

- The full Playwright journey passes through UI interactions from a clean environment.
- User name, organization, role badge, and logout are visible in every authenticated session.
- Server-side authorization rejects every tested forbidden command without mutation.
- Direct draft activation and invalid configuration transitions are rejected;
  the browser-visible evidence proves test, human approval, and prospective
  activation before downstream work begins.
- Real ingestion, extraction, correction, validation, package generation, return, resubmission, approval, and audit paths execute.
- Video, trace, and screenshots are retained as demo evidence.
- The auditor reconstructs both snapshot sets, all eight typed relation kinds,
  the return/correction/approval chain, and unchanged v1 snapshot/package
  hashes after v2 approval.
