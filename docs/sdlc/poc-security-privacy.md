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
