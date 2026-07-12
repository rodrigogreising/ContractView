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
- The required ContractView CI check has passed from two independent,
  fresh-volume Compose runs and retained its schema-valid evidence manifest.
- SUB-66 has reconciled all historical Done claims, received the applicable
  immutable-diff AI approvals, merged, and passed clean post-merge verification.
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
- Content-addressed validation input manifests with exact invoice snapshot,
  artifact, configuration, schema, mapping, rule, workflow, view/template, and
  extraction component versions.
- Attestation actors and exact invoice/package versions.
- Package manifests and distinct hashes for versions 1 and 2.
- Package reproduction manifests with versioned template/renderer contracts,
  deterministic generated-file digests, archive hashes, and replay results.
- Return feedback, revision relation, resubmission, approval, and audit-query evidence.
- Government return evidence contains a return-specific reason, normalized
  comment, and unique affected expense keys proven to belong to the exact v1
  invoice; final approval contains the corrected v2 package reference and no
  newly introduced affected-line claim.
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
- A return omits affected lines, cites a duplicate/foreign line, uses an
  approval reason, or changes queue/invoice/revision state after rejection.
- An approval uses a return reason, introduces affected lines, targets v1, or
  occurs without the prior return and corrected resubmission.
- Expense-date lineage points to a claimed-amount predecessor or a v2 correction
  skips the cloned same-field predecessor.
- Auditor cannot reconstruct the claimed amount and both packages.
- Replaying a retained validation/package input consults mutable current state,
  produces different results/bytes, or fails to detect a changed dependency.
- Playwright requires manual database changes or test-only role switching.

## Certification Criteria

- The full Playwright journey passes through UI interactions from a clean environment.
- User name, organization, role badge, and logout are visible in every authenticated session.
- Each session loads its contract context from the server-authorized context
  response; the production application bundle contains no fixed contract or
  seeded credential literal. The paced POC image enables the explicit demo
  credential boundary.
- Server-side authorization rejects every tested forbidden command without mutation.
- Direct draft activation and invalid configuration transitions are rejected;
  the browser-visible evidence proves test, human approval, and prospective
  activation before downstream work begins.
- Real ingestion, extraction, correction, validation, package generation, return, resubmission, approval, and audit paths execute.
- Video, trace, and screenshots are retained as demo evidence.
- The candidate merge is based on a passing required CI check whose manifest
  identifies its immutable base/head diff, exact tools, commands, exit codes,
  test counts, environment, and artifact hashes.
- The auditor reconstructs both snapshot sets, all eight typed relation kinds,
  the return/correction/approval chain, and unchanged v1 snapshot/package
  hashes after v2 approval.
- Replaying each retained validation input reproduces its findings/result hash,
  and replaying each package build input reproduces every generated file and
  the ZIP byte-for-byte. V1 remains unchanged while V2 has distinct input,
  reproduction-manifest, and archive hashes.

## SUB-46 Revision And Resubmission Certification

The returned-revision segment is certified only when the normal NGO Preparer
session receives the structured reason, note, exact line keys, immutable v1 id,
and editable v2 id. The server must reject correction of a different existing
v2 line with no change to the line, material revision, corrections, lineage, or
events. The accepted correction must append the Government decision reference
and same-field lineage successor.

After correction, deterministic validation must create a v2 run. A separately
authenticated NGO Approver must create a fresh attestation, package, and
submission for v2. Certification captures v1 package bytes/artifact hashes,
findings, feedback, aggregate events, and snapshots immediately after return
and proves exact equality after final v2 approval. V2 must link to v1 and have
distinct validation/build/archive identities. This issue certifies the journey
segment; SUB-55 still owns the paced Playwright video, trace, screenshots, and
clean end-to-end release decision.

## SUB-50 Read-Only Audit Reconstruction Certification

The normal Auditor login selects only a server-authorized contract and loads a
GET-only typed timeline. Certification requires the visible sequence from
configuration activation and source processing through correction, validation,
attestation, initial package/submission, return, revision, resubmission, second
package, and approval. Every event shows canonical user, organization, role,
time, aggregate/version references, and hash.

For the returned expense, the UI renders a source artifact/location, validation
run, immutable snapshot/version, and package path for both versions. V1 and v2
package/archive identities differ while captured v1 evidence remains unchanged.
The workspace has no mutation control; direct API mutation attempts are denied
with no durable state change. SUB-55 still owns browser pacing, screenshots,
trace, video, and the final clean-environment release decision.

## SUB-26 Canonical Browser Harness Certification

The entire journey is automated as one Playwright scenario from a clean,
isolated Compose environment. It uses the supported reset command, starts the
real worker afterward, and performs only visible UI actions plus explicit
negative HTTP authorization assertions. There are no manual database edits,
test endpoints, or test-only role switches.

The scenario logs in and out as Configuration Administrator, NGO Preparer, NGO
Approver, Government Reviewer, NGO Preparer, NGO Approver, Government Reviewer,
and Auditor. Every workspace assertion includes current user, organization,
role, permissions, and logout. Screenshots cover role workspaces, activation,
v1 validation/submission/return, v2 correction/resubmission/approval, and final
audit reconstruction.

Final assertions bind both captured archive hashes to their corresponding
EXP-004 audit trails, prove they differ, and prove the Auditor has no mutation
controls. Headless mode is the CI gate; headed mode defaults to paced `650 ms`
slow motion and emits the same video, trace, screenshots, JSON, and runtime
evidence. SUB-55 remains the terminal release certification of the merged
journey.

## SUB-53 Reproducible Operator Preconditions

Journey 11 can be invoked from a clean checkout with `make journey11-headless`
or `make journey11-headed`. Both commands delegate to the same isolated
SUB-26 scenario. Headed mode defaults to 650 ms pacing; both modes retain JSON,
video, trace, screenshots, HTML, runtime logs, and Compose state.

Normal local operation uses `make start`, `make reset`, and `make health`.
Reset stops the worker, replaces only disposable synthetic database/object
state through supported commands, applies numbered migrations, idempotently
seeds fixtures, restarts the worker, and prints the deterministic fingerprint.
No journey prerequisite requires SQL, role switching, or storage mutation.
