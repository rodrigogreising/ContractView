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

## SUB-66 Recovery AI And Configuration Decision

The 37-issue recovery audit confirms that no remediation grants runtime AI
authority. Extraction remains draft-only; deterministic shared rule contracts
own findings; versioned template contracts own package rendering; and canonical
humans alone govern configuration and perform attestation, submission, return,
and approval. Validation/package manifests retain provider, model, prompt,
parser, schema, mapping, rule, workflow, view/template, and configuration
versions without using AI during replay.

Decision: `Certified with exceptions` for development continuation after the
SUB-66 immutable review/merge gate. The narrow single-document-class evaluation
is explicitly owned as an exception and blocks expansion to new document
classes or real data until broader evaluation and privacy evidence exist.

## SUB-49 Government Decision Authority

SUB-49 contains no model call, prompt, confidence threshold, or AI-derived
decision input. A database-provisioned Government Reviewer alone may return or
approve. Return/approval reasons come from closed deterministic vocabulary;
affected lines are checked against the exact submitted invoice; state-machine
preconditions are deterministic; and event/package/version evidence is
append-only. Fabricated system/AI actors fail without mutation. This preserves
the prohibited-authority decision with no new AI configuration surface.

## SUB-46 Revision Authority

SUB-46 adds no model call, prompt, parser, threshold, or AI configuration. The
persisted Government decision deterministically selects the only correctable
line keys. A provisioned NGO Preparer supplies the human correction and reason;
a provisioned NGO Approver separately revalidates, attests, packages, and
resubmits. The correction event references the immutable decision and preserves
the original extraction/lineage chain. AI/system actors gain no correction,
validation, attestation, submission, return, or approval authority.

## SUB-50 Audit Projection Authority

SUB-50 invokes no model, prompt, parser, or confidence decision. The timeline
reads retained extraction provider/model/prompt/parser identifiers as evidence
only. Deterministic validation owns findings; canonical humans own corrections,
attestation, submission, return, and approval. The projection cannot create or
reinterpret those decisions, and replay does not call live AI.

## SUB-26 Browser Harness Authority

SUB-26 changes no model, prompt, parser, confidence rule, or AI authority. The
browser observes the existing local worker's supported synthetic extraction and
requires NGO human correction before deterministic validation. All validation,
attestation, submission, return, correction, resubmission, approval, and audit
outcomes continue to be owned by shared deterministic contracts or canonical
human actors. Playwright proves those boundaries; it does not bypass or replace
them.

## SUB-53 Operator AI Boundary

SUB-53 adds no provider, model, prompt, parser, threshold, evaluation class, or
AI-generated configuration. The runbook explicitly records that the supported
adapter is local, requires no external credential, produces draft fields only,
and sends no bytes to a third party. Operator commands cannot turn AI output
into deterministic validation or a human-authority action.

## SUB-55 Terminal Journey AI Boundary

SUB-55 changes no provider, model, prompt, parser, schema, threshold, supported
document class, or configuration authority. The recorded browser journey
observes the local adapter create draft fields, requires an NGO Preparer to
correct the intentionally wrong proposed value, and only then executes shared
deterministic rules. Separate canonical humans perform configuration approval,
attestation, submission, return, correction, resubmission, and final approval.

The final replay evidence verifies retained provider/model/prompt/parser
identifiers without calling live AI. The permission summary is derived from
the closed role vocabulary and grants no action. A system or AI actor remains
unable to activate configuration or perform any human-authority transition.

## SUB-74 Configurable Document-Intake MVP AI And Configuration Decision

The successor MVP deliberately adds no runtime AI capability. Pinned local OCR
is a replaceable extraction adapter and its exact version is a deterministic
input; it is not profile, validation, or workflow authority. Profile matching,
normalization, ledger reconciliation, cluster fingerprinting, validation,
workflow, and package generation use declared deterministic contracts.

Hosted model calls, runtime LLM extraction, external model credentials,
AI-assisted profile drafting, opaque classification, and automatic cluster-to-
profile assignment are prohibited. A cluster is a noncanonical suggestion. An
assigned human Configuration Administrator must confirm a draft association,
test immutable fixtures, approve the exact profile version, and activate a
prospective configuration bundle. System and AI actors have empty authority
sets.

The fixture evaluation is a closed, versioned synthetic test set containing at
least two English and two Spanish supported invoices, one changed layout, one
unknown layout, and one successor historical replay. Required normalized
fields/source locations must be 100% exact; changed/unknown safe routing must be
100%; canonical mutation and automatic assignment must be zero. Evaluation
records retain fixture-set, expected-record, OCR/parser, fingerprint, profile,
and configuration versions plus content hashes.

The historical POC AI record remains valid only for the certified Journey 11
baseline. It neither authorizes nor supplies runtime AI behavior for Journey
12. Any future proposal to add model-assisted profile drafting or hosted
extraction is a new scoped governance decision with separate data approval,
evaluation, failure thresholds, human-review rules, and release gate.

## SUB-75 Deterministic Configuration Evidence Decision

SUB-75 adds no provider, model, prompt, parser, confidence threshold, hosted
call, profile classifier, or AI-generated configuration. The applicable
configuration suite remains `configuration-governance-v1`, and every check is
deterministic over the exact canonical JSON payload. Testing retains the suite,
individual checks, payload hash, and result hash as immutable evidence.

Approval remains a canonical human Configuration Administrator action bound to
the exact test-evidence id. Activation and supersession independently
recompute the payload hash, expected report, result hash, suite version, and
approval hash. A system/AI actor, stale client, lifecycle label, failed report,
or unbound approval cannot activate a version.

Human-readable diff, prospective impact, and runtime-reference responses are
deterministic noncanonical projections. They explain retained evidence but do
not evaluate compliance, assign a profile, make a validation finding, or grant
authority. Replaying unchanged immutable inputs produces identical projection
hashes. Profile fixture evaluation and the pinned local OCR behavior remain
deferred to SUB-76 under the stricter Journey 12 metrics already defined above.

## SUB-76 Deterministic Extraction And Evaluation Decision

SUB-76 adds no runtime AI. `tesseract-5.5.0-eng+spa` is a pinned local OCR
adapter whose output is untrusted draft input. Profile parsing, normalization,
fingerprinting, cluster projection, exact matching, ledger reconciliation,
safe routing, fixture evaluation, validation, and package inputs are
deterministic shared-contract behavior.

The closed evaluation suite records fixture-set, expected fields/source
locations, OCR model, parser, fingerprint specification, profile version,
configuration reference, exact metrics, and content hashes. Supported English
and Spanish cases require 100% field and source-location exactness;
changed/unknown cases require 100% safe routing and zero canonical mutation.
Identical declared inputs reproduce fingerprint, normalized draft, match, and
result hashes.

Cluster projections remain noncanonical and cannot assign profiles. System and
AI actors still have no create, test, approve, activate, supersede, retire,
validate, attest, submit, return, or approve authority. Any hosted model,
model-assisted profile drafting, fuzzy automatic assignment, or expanded data
class requires a new governance decision and evaluation gate.

Configuration rollback remains deterministic human-governed execution. It may
reactivate an exact historical profile only through a newly tested and approved
configuration version and an append-only `profile_rollback_activated` event.
