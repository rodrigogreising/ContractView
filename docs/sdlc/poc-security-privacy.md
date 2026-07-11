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
