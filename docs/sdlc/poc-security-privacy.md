# POC Security And Privacy Review

## Human Decision Enforcement

Government return and approval require both the Government Reviewer policy and a database-backed seeded user whose role and organization match the server actor. Fabricated system or AI identities cannot make decisions. Stale or out-of-order queue actions fail before mutation, and decision records are append-only.
Status: Approved for synthetic-data POC

## Data Decision

Only synthetic, non-branded organizations, users, ledgers, receipts, contract terms, feedback, and packages may enter the POC. Real employee, client, bank, tax, health, customer, employer, or service-recipient data is prohibited.

## Sensitive Flows

- Seeded passwords are development secrets stored as hashes; plaintext demo credentials are documented only for the local synthetic environment.
- Cookie sessions use HTTP-only cookies, same-site protection, expiry, revocation on logout, and secure mode outside localhost.
- Uploads are restricted by configured type and size, hashed, tenant-scoped, and stored in MinIO.
- OCR/LLM requests contain synthetic fixture data only and use the minimum required pages/fields.
- Generated packages remain synthetic but are protected by the same authorization rules as uploads.
- Playwright video/traces may show demo credentials and synthetic data; artifacts are not production evidence.

## Threats And Mitigations

| Threat | Mitigation |
| --- | --- |
| Role escalation | Server-side RBAC and resource checks; forbidden-command tests |
| Session reuse after logout | Server revocation and Playwright assertion |
| Cross-organization reference | Organization scope on queries, commands, jobs, artifacts, and audit views |
| Submitted version mutation | Database invariants plus immutable object hashes |
| Malicious upload | POC type/size validation; clearly defer malware scanning before real data |
| Prompt/document injection | Synthetic constrained document class; treat extraction as untrusted draft |
| Secret leakage | Environment variables, ignored local secrets, redacted logs |
| Test backdoor | Prohibit role-switch endpoints and manual database mutation in certification |

## SUB-60 Tenant Authorization Recovery

Controlling issue: `SUB-60` / REC-04. Project stage: Build.

### Data classification and access paths

- Contract ownership, user organization, persona role, contract-role assignment,
  invoice lifecycle, and artifact publication state are authorization data.
- The fixture contains synthetic identities and organizations only. Assignment
  rows do not authorize real customer, employee, client, bank, tax, or health
  data.
- Protected API/application commands resolve scope from PostgreSQL contract and
  resource records. A request parameter or actor-authored `ResourceScope` is
  never accepted as ownership evidence.
- Configuration administrators require an explicit active-user assignment to
  the canonical contract and agency. Auditors require an explicit assignment
  and may read only canonically submitted resource kinds.
- Audit reconstruction filters events and lineage by submitted invoice,
  artifact, validation, extraction, configuration, package, and decision
  references. A submitted contract does not make later draft-only events
  visible to the auditor.
- Submission atomically publishes the original ledger/evidence artifacts and
  linked extraction source/raw-response artifacts as well as generated package
  artifacts. The auditor can therefore traverse submitted source evidence
  without gaining access to unrelated drafts.

### Threat model and mitigations

| Threat | Executable mitigation and evidence |
| --- | --- |
| Caller claims a favorable tenant | Noncanonical scopes fail closed for every role/action; `test_caller_authored_scope_claims_fail_closed` covers the matrix. |
| Administrator guesses another contract | `configuration_scope` joins the active user, role, assignment, canonical agency, and contract; the rejected command has an identical database mutation fingerprint. |
| User follows an indirect foreign artifact id | `artifact_scope` resolves the artifact's persisted contract and publication state before object-store access; cross-tenant denial leaves all material table counts unchanged. |
| Auditor reads draft work | Auditor policy requires assignment, submitted state, read action, and an allowlisted immutable/read-model resource kind. Draft artifacts, jobs, extraction review, configuration drafts, and draft-only audit events are denied. |
| Auditor loses submitted source lineage | Submission publishes every source/raw-response artifact referenced by the exact invoice version; integration tests download those artifacts as the assigned auditor and reconstruct extraction, review, validation, attestation, package, and submission events. |
| Assignment is internally inconsistent | Migration `019_contract_role_assignments.sql` rejects assignments whose agency, active user, or provisioned role does not match canonical data. |
| Denied action partially mutates state | Authorization runs before command callbacks; database-backed direct and indirect denial tests compare counts across configuration, artifacts, jobs, reviews, invoices, validation, workflow, events, and lineage. |
| AI or system receives human authority | The policy adds no authority role. NGO Approver and Government Reviewer controls remain distinct; administrator and auditor assignments cannot attest, submit, return, or approve. |

### Retention and deletion decision

Contract-role assignments are durable authorization records for the synthetic
POC and are recreated by the deterministic fixture reset. Submitted evidence
and its audit projection retain their existing immutable/append-only behavior.
Automated revocation history, retention schedules, deletion, legal hold,
backup, and disaster recovery remain outside the local POC and must be designed
before real or hosted data is permitted.

### Review and release impact

- Required AI reviews: `cv-review-security-privacy`,
  `cv-review-boundary-review`, and `cv-review-implementation-tests` against the
  immutable PR base/head.
- Human code review is not required. No real-world risk acceptance or human
  authority action is being performed by this code change.
- Release-facing work remains blocked on REC-12 recertification and Journey 11;
  SUB-60 removes the known tenant-scope blocker but is not a release decision.
- Accepted POC risk: authorization denials are proven by retained test evidence
  but are not yet stored as a complete permission-decision event stream.
  REC-08/REC-11 must reconcile versioned evidence and durable CI retention.
- Accepted POC risk: scope lookup and command mutation use separate short-lived
  transactions. There is no assignment-management path in the synthetic POC;
  REC-07 must place assignment checks and commands under capability-owned unit
  of work semantics before real or hosted use.

## Accepted POC Risks

- No MFA, password recovery, invitation, or enterprise SSO.
- No malware scanner.
- No automated retention, deletion, legal hold, backup, or disaster recovery.
- No production penetration test or hosted security review.

These risks are acceptable only because the environment is local, synthetic, and non-production. Any real or hosted data use reopens security/privacy review.

## SUB-67 CI Evidence Security

Controlling issue: `SUB-67` / REC-11. Project stage: Build.

- CI accepts only repository synthetic fixtures and creates isolated database
  and object-store volumes for each pass. It does not ingest customer or pilot
  data.
- Workflow permissions are read-only. Official Actions and container bases are
  content-addressed, preventing an upstream floating tag from silently changing
  the reviewed environment.
- Retained evidence contains test output, Compose service state, semantic reset
  fingerprints, versions, commands, SHAs, counts, and artifact hashes. It must
  not contain environment secrets, session cookies, uploaded document content,
  or database dumps.
- GitHub retains the CI artifact for 30 days. Durable approval and completion
  claims remain in the repository/PR/Linear evidence chain; CI logs do not
  replace immutable application provenance.
- Human code review is not required. Executable certification plus applicable
  immutable-diff AI reviews are the code gate. Real release promotion and
  runtime human-authority decisions remain separate explicit approvals.

## SUB-63 Configuration Lifecycle Recovery

Controlling issue: `SUB-63` / REC-06. Project stage: Build.

- Every lifecycle command resolves the canonical contract and requires the
  persisted active Configuration Administrator assignment introduced by
  SUB-60. A caller-supplied role, organization, or contract claim is not an
  authority source.
- Testing and approval record the assigned human administrator identity, role,
  organization, rationale, and immutable hashes. Database constraints prohibit
  system/AI roles in these records.
- Direct draft-to-active, skipped approval, parallel activation, stale
  supersession, active retirement, foreign-contract rollback, and unauthorized
  actions fail before mutation. Tests compare governance-table fingerprints for
  direct and authority denials.
- Definition snapshots, test evidence, approvals, and lifecycle events are
  append-only. The current-active projection is capability-owned and changes
  only inside the same transaction that appends the corresponding lifecycle and
  domain events.
- The API integration test uses the normal server-issued cookie session and
  logout. The UI does not provide test-only role switching or client-only
  authorization.
- All data and rationales in the POC remain synthetic and non-branded. This
  lifecycle does not approve production configuration or real-world use.

Required immutable-diff AI reviews are security/privacy, AI/config governance,
architecture, boundary, traceability, journey, and implementation. Human code
review is not required; human participation is retained only where the runtime
business action itself is explicitly human authority.

## SUB-64 Provenance And Immutable Snapshot Recovery

Controlling issue: `SUB-64` / REC-08. Project stage: Build.

- Material events derive actor role and actor organization from the canonical
  user record; the separately recorded resource organization preserves tenant
  scope. Incomplete envelopes are rejected at the database boundary.
- Invoice snapshots bind the exact contract, NGO organization, invoice version,
  material revision, configuration, line data, artifact hashes, and mapping
  versions. Append-only triggers protect snapshots, relations, validation runs,
  and validation results from update or deletion.
- Auditor queries ignore the compatibility `submitted` argument and derive
  visibility from canonical invoice state and assignment policy. Draft-only
  snapshots, events, and relations remain unavailable to the Auditor.
- Government relations retain the government reviewer as actor while the
  related invoice remains owned by the NGO organization. This prevents actor
  context from being confused with resource tenancy.
- Denial and immutability tests prove zero mutation, v1 preservation, and
  reconstruction of corrected v2. All fixtures remain synthetic and local.

Residual POC risk: the evidence store is local PostgreSQL/MinIO without hosted
backup, legal hold, retention automation, or external timestamping. Those
controls are required before real data or production use.

## SUB-68 Reproducibility Evidence

Controlling issue: `SUB-68` / REC-09. Project stage: Build.

- Validation and package manifests are organization/contract-scoped runtime
  evidence assembled only after canonical authorization and ownership checks.
- Manifests retain identifiers, versions, hashes, rule inputs, findings, and
  synthetic invoice values; they do not retain passwords, sessions, provider
  credentials, or raw model secrets.
- Append-only database triggers protect manifests and validation results.
  MinIO reads recompute artifact hashes before reproduction can succeed.
- Auditor reconstruction uses the existing assignment-scoped read model;
  callers cannot select a foreign organization or grant themselves visibility.
- Replay is read/compute verification. It cannot mutate invoice state, activate
  configuration, attest, submit, return, or approve.

Residual POC risk remains local evidence retention without hosted backup,
external timestamping, legal hold, or automated deletion. All retained values
are synthetic and non-branded; real or hosted data requires a new review.

## SUB-65 Web Session And Demo Boundary

Controlling issue: `SUB-65` / REC-10. Project stage: Build.

- The browser obtains contract identifiers only from `/auth/contracts`, whose
  query derives NGO/agency ownership or explicit administrator/auditor
  assignments from the canonical server session.
- Client role workspaces are presentational. Every API command retains its
  existing server authorization and zero-mutation denial behavior.
- Seeded emails/passwords live only in `src/demo` and compile into explicit
  demo/test builds. The default production build contains no demo credential or
  fixed contract literal.
- Transport errors are normalized centrally; feature modules cannot silently
  treat a failed response as authorized data.
- All identities and contexts remain synthetic and reserved-domain. This does
  not add real identity provisioning, SSO/MFA, or hosted deployment.

Residual POC risk: the demo Compose build intentionally exposes synthetic
credentials for a local recorded journey. It must never be promoted as a
production build; real identity lifecycle remains deferred.

## SUB-79 Public Disclosure Boundary

Controlling issue: `SUB-79`. Project stage: Build.

- The private repository remains the durable SDLC and audit store. It is not
  itself the public artifact because its Git history and control-plane evidence
  contain identities and links outside the approved disclosure boundary.
- Publication uses a deterministic allowlisted, history-free export with a
  neutral repository identity. Internal implementation evidence, Linear and PR
  links, local artifacts, and publication tooling are excluded.
- Runtime fixtures use a positive synthetic-data contract: closed organization,
  persona, vendor, employee-reference, and reserved-domain email catalogs. The
  generated CSV, XLSX, PDF, and PNG artifacts are deterministic and their
  content, metadata, and hashes are verified.
- The candidate verifier rejects legacy/private identity fragments,
  non-reserved email domains, Git metadata, and high-confidence secret shapes.
  It records every included path and SHA-256 digest in
  `PUBLICATION-MANIFEST.json`.
- SUB-79 does not change repository visibility or grant a reuse license. A
  separately recorded owner disclosure decision is required after the
  candidate passes clean Compose certification and immutable AI review.

## SUB-66 Recovery And Current Public Visibility

Controlling issue: `SUB-66` / REC-12. Project stage: Evidence Review.

- GitHub reports the durable `rodrigogreising/ContractView` repository as
  `PUBLIC`. This owner action occurred after SUB-79 certified a separate
  allowlisted, history-free candidate.
- The current public repository intentionally exposes Git author history,
  owner identity, SDLC evidence, issue identifiers, and PR/Linear links that
  SUB-79 excluded. SUB-66 invalidates any claim that the candidate's anonymity
  or control-plane exclusions describe this repository.
- The tracked tree contains no detected high-confidence secret shapes outside
  the scanner and its negative test fixtures. Runtime fixture generation uses
  positive closed synthetic catalogs, reserved-domain identities, deterministic
  binary metadata, and hash manifests.
- GitHub's secret-scanning API reports the repository feature disabled. The
  current-tree scan is a compensating control, not a substitute; enabling the
  hosted control is part of the accepted disclosure exception's resolution.
- The visibility decision does not change tenant authorization, immutable
  provenance, AI authority, configuration governance, or runtime data scope.
  Real data remains prohibited.
- The disclosure is an owner-accepted exception, not an open-source license.
  The all-rights-reserved `LICENSE` remains controlling. Before a claim of
  history-free/privacy-neutral publication or open-source distribution, use the
  certified candidate or separately certify the full-history disclosure.

SUB-66's security decision is `Certified with exceptions` for return to Build
only after immutable AI review, merge, and clean post-merge verification.
Journey 11 and any staging/production promotion remain separately blocked.

## SUB-49 Government Human-Authority Evidence

Controlling issue: `SUB-49`. Project stage: Build.

- Authorization resolves the queue/invoice/package contract and agency from
  canonical records. The caller cannot supply organization or ownership scope.
- A Government Reviewer actor must match an active provisioned database user,
  role, and organization. Fabricated system/AI identities and NGO roles fail
  before the decision callback mutates state.
- Return reasons and approval reasons are disjoint. Notes are normalized and
  required. Return line keys must be nonblank, unique, and present on the exact
  submitted invoice; approval cannot inject affected-line evidence.
- Denial tests compare decision count, revision-link count, queue status, and
  invoice state before and after empty, foreign, duplicate, and wrong-reason
  attempts.
- Material events preserve Government actor organization separately from NGO
  resource organization and bind exact invoice, submission, package, and
  decision versions.

All values remain synthetic. This closes the POC human-authority and
cross-reference risk for the return/approval command; it does not authorize
real-data or production review.

## SUB-46 Revision Authorization And Immutability Evidence

Controlling issue: `SUB-46`. Project stage: Build.

- Canonical invoice scope and explicit assignment authorize the returned draft;
  organization and contract ownership are never accepted from the request.
- The server binds a correction to the persisted predecessor/successor link and
  exact Government decision line keys. A valid line elsewhere in the same draft
  is still rejected, with zero mutation across its line value, material
  revision, correction records, lineage, and events.
- NGO Approver cannot correct. NGO Preparer cannot attest, package, submit, or
  make Government decisions. A separate provisioned NGO Approver must re-attest
  and resubmit v2 after deterministic revalidation.
- V1 package object bytes and artifact hashes, validation findings, feedback
  decision, material events, and immutable snapshots are captured after return
  and compared after v2 approval. Database append-only guards remain active.
- The UI renders only returned line keys and disables correction when persisted
  feedback cannot be matched to the editable draft; this is defense in depth,
  not the authorization boundary.

All tested identities and records remain synthetic and reserved-domain. This
does not add real-data handling, hosted retention, SSO/MFA, or production
promotion authority.

## SUB-50 Auditor Scope And Zero-Mutation Evidence

Controlling issue: `SUB-50`. Project stage: Build.

- The server resolves audit access from canonical contract assignment and
  submitted invoice state; query parameters do not grant tenant visibility.
- `/audit/timeline` is GET-only. The Auditor workspace receives no mutation
  callback and renders no form or action button.
- HTTP denial tests exercise configuration, invoice assembly, validation,
  attestation, package, and submission commands under a real Auditor session
  and compare mutation-sensitive table counts before and after.
- Actor identity is enriched from canonical users; typed events and relations
  preserve actor and resource organizations separately.
- Only submitted evidence is returned; draft-only evidence remains hidden.

All content remains synthetic and reserved-domain. This adds no broader
retention, real-data, public-write, support-access, or production authority.

## SUB-26 Browser And Artifact Security Evidence

Controlling issue: `SUB-26`. Project stage: Build.

- The browser uses normal server-issued sessions; every persona logs out before
  the next login, and no role-switch or session-injection helper exists.
- Configuration Administrator and Auditor sessions make direct forbidden API
  requests and require server `403` responses. Auditor UI contains no form or
  action button.
- The journey uses only the deterministic synthetic fixture pack. Video,
  screenshots, trace, HTML, logs, and JSON therefore contain demo identities
  and synthetic values only; they remain development certification evidence.
- The Compose project and volumes are unique per run, the web test port is
  private, and cleanup removes all isolated state unless an explicit diagnostic
  retention flag is set.
- Captured v1/v2 hashes are asserted through the server-owned audit projection;
  Playwright does not write or synthesize provenance.

This certifies the POC browser path. It does not authorize real data, public
write access, production credentials, hosted deployment, or production artifact
retention.

## SUB-53 Operator Credential And Evidence Boundary

Controlling issue: `SUB-53`. Project stage: Build.

- The runbook names only public synthetic demo credentials and explicitly
  prohibits their reuse or the introduction of real data.
- The active local Tesseract/fixture parser needs no external provider key and
  sends no source artifact outside the Compose project.
- Toolchain checks fail before Compose mutation. Host port overrides permit an
  isolated concurrent project without weakening container scope.
- Normal stop preserves local named volumes; certification projects destroy
  their isolated state after retaining browser/runtime evidence.
- Reset is allowed only for disposable synthetic state. It is not a production
  deletion, retention, or legal-hold mechanism.

This adds no public write path, hosted credentials, customer data, support
access, production storage, or production promotion authority.

## SUB-55 Terminal POC Security Evidence

Controlling issue: `SUB-55`. Project stage: Evidence Review.

- Every authenticated header visibly states the current synthetic user,
  organization, role, bounded permission summary, and logout. The summary is
  usability evidence only; application authorization still resolves the
  canonical session, assignment, resource, lifecycle state, and action.
- The canonical journey uses distinct server-issued sessions and logs out
  before every persona handoff. Direct forbidden API commands must return `403`
  and existing zero-mutation integration tests remain part of the static and
  hermetic gates.
- Browser media, traces, HTML, logs, and machine results contain only the
  closed synthetic fixture catalog and reserved-domain identities. No external
  provider credential or customer data enters the run.
- Unique Compose projects and fresh PostgreSQL/MinIO volumes isolate candidate
  and headed-demo runs; retained evidence is hashed before the environment is
  destroyed.

Residual risks remain the accepted local synthetic-POC exclusions: no hosted
retention/backup/legal hold, SSO/MFA, malware scanning, real-data approval, or
production penetration test. The public full-history/license/hosted-secret-
scanning exceptions are unchanged. This certification cannot promote staging,
production, or real data.

## SUB-74 Configurable Document-Intake MVP Security And Privacy Decision

SUB-74 expands design scope, not the approved data class. All profile fixtures,
vendor aliases, users, organizations, contracts, and artifacts must come from
closed synthetic catalogs and deterministic generators. Acceptance checks
validate those positive catalogs and their generation/provenance contracts;
they do not rely on a blacklist of brand names or sensitive terms.

English and Spanish are source-document profile tags only. Source bytes remain
inside the local synthetic runtime and are never sent to a hosted model. Pinned
local OCR may read the bytes; exact artifact, OCR/parser, profile,
configuration, source-location, and human-review references are retained.
Changed or unknown layouts create `needs_profile_review` and no canonical
expense, validation result, automatic profile assignment, or activation event.

Every profile command/query resolves canonical contract/agency ownership and
the administrator's explicit assignment. Indirect artifact, fixture,
evaluation, cluster, predecessor, successor, or bundle references must resolve
to the same authorized scope before mutation. Auditor access remains explicit,
submitted-scope, and read-only. Denials for direct and indirect cross-tenant,
stale, invalid-transition, and wrong-role requests must leave all owners'
tables and object storage unchanged.

The new profile/evaluation records use the existing local POC retention
boundary: immutable evidence is retained for reconstruction, no real-data
retention or deletion claim is made, and release remains blocked for hosted or
production use. Residual risks are conservative false review routing for benign
layout changes and the certified POC's local-only identity, malware-scanning,
backup, legal-hold, penetration-test, SSO, and MFA exclusions.

## SUB-75 Configuration Lifecycle And Provenance Security Decision

SUB-75 changes configuration governance behavior without expanding the
approved synthetic/local data boundary. Draft payloads, test reports,
approvals, version details, diffs, impacts, runtime references, UI output, and
retained test evidence contain only the existing closed synthetic fixture and
reserved-domain identities.

Every full-history read and mutation resolves the configuration version or
contract from persisted ownership, then checks the actor's explicit
Configuration Administrator assignment. Caller-provided organization or role
claims never become scope. NGO and Government personas receive only the
existing scoped active summary; Auditor data continues through its explicit
submitted, read-only audit projection. Direct version detail, diff, impact,
reference, and mutation attempts by wrong-role or unassigned actors are denied
before mutation.

Editable drafts carry a server-stored positive revision. Save and test compare
the expected revision under the owner transaction. Stale, cross-scope,
unauthorized, invalid-transition, failed-evidence, or incorrectly bound
approval requests append no configuration version, test, approval, lifecycle,
active pointer, or domain event. Activation and supersession recompute exact
payload/test/result/approval hashes and require the current pinned deterministic
suite to pass.

The runtime-reference join is a declared, read-only projection over stable ids
and immutable records. It is reachable only through the read-model repository,
owns no table, exposes no raw SQL/query builder, and cannot mutate source
owners. Projection responses state `canonical=false` and are content hashed.
Migration 024 adds read-support indexes and draft concurrency only; it creates
no duplicate canonical state.

Residual risk is unchanged from the local MVP boundary: the UI is not a
production configuration console, sessions lack production SSO/MFA controls,
and retained evidence has no hosted retention/legal-hold claim. These changes
do not authorize real data, public writes, external credentials, production
activation, or cross-tenant disclosure.

## SUB-76 Deterministic Profile Security Decision

SUB-76 processes only the closed synthetic English/Spanish fixture catalog in
the local Compose boundary. Pinned Tesseract reads source bytes locally; no
hosted model, external credential, customer identity, or network data transfer
is introduced. Fixture acceptance uses positive catalog and generator
provenance with deterministic hashes, not a forbidden-term blacklist.

Every profile command first resolves the persisted contract and explicit
Configuration Administrator assignment. Database constraints separately bind
authority evidence to that contract/role assignment and to the actor's
canonical user organization. Wrong-role cluster confirmation and profile
mutation fail without changing profile, active-assignment, invoice, validation,
or cluster-association counts.

Changed, unknown, incomplete, and unmatched documents are untrusted inputs.
They retain immutable artifact/OCR/fingerprint/match evidence and a
noncanonical suggestion but create no canonical expense or automatic profile
assignment. Profile, evaluation, approval, lifecycle, fingerprint, match, and
association records reject update/delete. Residual risks remain the local POC
identity, malware-scanning, backup, legal-hold, SSO/MFA, and production
hardening exclusions.

Adversarial layout evidence retains valid labels and values but inserts
undeclared non-empty rows; it is denied exact matching and creates no fields or
canonical state. Profile creation also rejects negative-only, single-positive,
cross-profile-predecessor, and undeclared-fingerprint inputs before governed
mutation. Configuration testing resolves exact profile/evaluation/approval
evidence, so guessed or hash-mismatched profile references cannot acquire a
passing tested or approved configuration state.

## SUB-77 Administrator Workspace Security And Privacy Decision

SUB-77 adds a browser projection only and does not expand the approved local,
closed-synthetic data class. Configuration, profile, fixture, evaluation,
cluster, artifact, actor, and contract values come from normal
session-authenticated server responses. Fixture transcripts are not rendered;
only governed filenames, expected outcomes, exact metrics, ids, versions, and
hashes are shown.

The client never accepts caller-supplied organization, role, lifecycle state,
approval, or activation evidence. Every query and command remains scoped by
the canonical session, persisted contract ownership, and explicit
Configuration Administrator assignment. Wrong-role, unassigned, cross-scope,
stale, and invalid-transition requests remain server denials with the existing
zero-mutation guarantees; hidden or disabled buttons are not treated as an
authorization boundary.

Profile-reference staging writes only the authorized editable configuration
draft. Cluster confirmation writes only a draft association. Neither path can
activate a profile, create a canonical invoice expense, validate, or perform a
human-authority action. Explicit activation confirmation documents the
operator's intended future-only scope but cannot override server evidence or
historical-reference preservation.

The authenticated shell exposes loading, empty, failure, and unauthorized
states through accessible status/alert regions. The local retained browser
evidence contains reserved-domain identities and synthetic fixture metadata
only. The existing POC exclusions for production identity, retention,
malware scanning, penetration testing, and real-data approval remain.
