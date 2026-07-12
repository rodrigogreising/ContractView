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
