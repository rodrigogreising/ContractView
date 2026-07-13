# Release Certification

Release certification defines the minimum evidence required before a ContractView version can be called capable of executing its reimbursement workflow job end to end.

## Certification Decision

Each release candidate must end with one decision:

- Certified.
- Certified with exceptions.
- Blocked.

Exceptions must identify owner, risk, compensating control, target resolution, and whether the release is still safe for the pilot scope.

## Required Release Checklist

| Gate | Required evidence | Pass condition |
| --- | --- | --- |
| Requirements coverage | Requirement-to-journey and requirement-to-ADR mapping. | No MVP-critical requirement lacks coverage. |
| Architecture coverage | Updated architecture docs and ADRs for material changes. | Service/package ownership and boundaries are current. |
| Deterministic validation | Rule tests, validation-run evidence, stable re-run evidence. | Same inputs and configuration versions produce same outputs. |
| Configuration governance | Active configuration bundle versions and approval records. | Production configuration is tested, approved, and versioned. |
| Provenance | Artifact hashes, events, lineage, validation runs, package manifests. | Certified journeys can be reconstructed. |
| Human authority | Permission and actor evidence for attestations, waivers, returns, approvals, and finalization. | No system or AI actor performs human-authority actions. |
| Security/privacy | Threat model and data-governance review for in-scope sensitive flows. | High-risk gaps are mitigated or explicitly accepted. |
| AI governance | Evaluation record and traceability for AI-assisted behavior. | AI remains advisory or draft-producing where required. |
| Operational readiness | Runbooks for in-scope jobs, integrations, support access, and incidents. | Production support path is defined. |
| Known risks | Risk register and accepted exceptions. | Release owner signs off on remaining risks. |

## MVP-Critical Journeys

For the first pilot release, certification should include:

- Nonprofit upload to draft invoice.
- Validation failure and issue resolution.
- Nonprofit approval and submission.
- Agency review and return.
- Resubmission after return.
- Agency approval and payment-status update.
- Auditor reconstruction of submitted claim.
- Support/admin configuration change with audit visibility.
- AI-assisted extraction requiring human correction if AI extraction is enabled.
- Config/rule version change applied prospectively.

## Role-Based POC Certification

The engineering POC is certified separately from a production or customer pilot. Its controlling evidence is Journey 11 and the passing recorded Playwright run. Production operations, customer data controls, payment, notifications, broad extraction evaluation, and business outcome metrics are explicitly deferred.

POC certification still blocks on:

- Runtime AI creating validation or authority decisions.
- Client-only role enforcement.
- Role switching through test backdoors.
- Mutable submitted package versions.
- Missing source-to-approval provenance.
- Manual database edits required to complete the canonical journey.

## Evidence Quality Requirements

Evidence must be:

- Linked to the release candidate version.
- Tied to fixture data or production-like pilot data.
- Reproducible or exportable.
- Specific enough to identify actors, timestamps, configuration versions, artifact versions, validation runs, and package hashes.
- Stored in a location covered by retention policy.

### Automated Candidate Certification

Every candidate first passes the required `ContractView CI / certification`
check. The check uses exact tool and container pins, runs static/architecture/
boundary/test/build gates, executes the full runtime twice with separately
created PostgreSQL and MinIO volumes, and retains a schema-valid manifest with
base/head SHAs, commands, exit codes, versions, exact test counts, timestamps,
and artifact hashes. Applicable `cv-review-*` skills then review that immutable
diff and its executable evidence. Human code review is not a default gate.

This automated candidate decision does not impersonate an NGO Approver,
Government Reviewer, Configuration Administrator, or a human decision to
promote a real release. Journey 11 and release-scope authority evidence remain
required where those actions are explicitly in scope.

### Reproducible Runtime Evidence

For validation/package changes, candidate evidence must prove more than a
stable test name. The retained validation input manifest binds an immutable
invoice snapshot and artifact hashes to exact configuration, schema, mapping,
rule, workflow, view/template, and parser/model versions. The retained package
reproduction manifest binds a versioned template/renderer contract, canonical
claim columns, validation identity, generated-file hashes, and archive hash.

Certification replays both paths from retained inputs and independently checks
result/file hashes. Identical inputs must reproduce exactly; a changed input
must create a distinct traceable version. A passing live generation that cannot
be replayed from its retained evidence is blocked.

### Web Boundary Certification

Production-facing web candidates must exclude seeded credentials and fixed
contract selection. Contract context comes from the authenticated server and
generated shared DTOs. CI verifies that only the transport module performs
network requests, capability/role modules remain presentational, API errors are
handled explicitly, and the default production bundle contains neither demo
credential nor synthetic-contract literals. Demo credentials require an
explicit demo/test build flag.

### Recovery Baseline Gate

SUB-66 records a candidate decision of `Certified with exceptions` for the
development baseline only. Its machine-readable record audits all 37 historical
Done issues, invalidates provisional legacy approvals, proves all ten recovery
prerequisites are merged and post-merge verified, and keeps SUB-26, SUB-50,
SUB-53, and SUB-55 blocked until the SUB-66 PR itself is approved, merged, and
cleanly verified. This gate permits return to Build; it does not certify Journey
11 or authorize staging/production promotion.

The repository owner has made the durable repository public. That disclosure
is broader than SUB-79's history-free allowlisted candidate and is retained as
an explicit owner-accepted exception. It must not be described as a
history-free, anonymous, or open-source artifact; runtime fixture and secret
controls remain separately certified.

### Government Decision Certification

SUB-49 return/approval evidence must prove more than a changed workflow status.
A v1 return requires a return-specific reason, normalized note, and at least one
unique affected expense key from the exact submitted invoice. Invalid evidence,
unauthorized/system/AI actors, stale commands, duplicate return, and
out-of-order approval must leave decision, revision, queue, and invoice state
unchanged. Final approval requires a corrected later submission and binds the
canonical Government actor plus exact invoice, submission, package, and
decision versions. Passing SUB-49 unblocks correction/resubmission; it does not
replace the final Journey 11 recording.

### Returned Revision Certification

SUB-46 must prove that a correction is authorized against the canonical
returned successor and the exact affected line set in its immutable Government
decision. An unrelated existing v2 line, an unauthorized role, a non-draft
invoice, or incomplete correction input must produce zero mutation. The
accepted correction records normalized values, the human Preparer, same-field
lineage, material revision, and the decision version reference.

The same integration path must then execute deterministic v2 validation and a
separate NGO Approver attestation, package, and resubmission. V1 package bytes
and hashes, findings, feedback, events, and snapshots must remain byte/value
identical; v2 must retain its predecessor/decision link and distinct validation,
package-build, and archive hashes. Passing SUB-46 unblocks the audit timeline;
it does not replace the final clean Playwright recording or release review.

### Public Repository Publication

Public source disclosure is a separate release decision from POC runtime
certification. A public candidate must:

- be produced from an explicit allowlist under a neutral repository identity;
- use only synthetic identities and reserved-domain contact data;
- exclude Git history, private control-plane evidence, local artifacts, and
  publication tooling;
- include a security policy and an explicit rights notice;
- include a machine-readable source SHA, path, file-hash, scan, environment,
  command, exit-code, test-count, and evidence-artifact manifest; and
- pass its own clean-database API, frontend, build, and Compose regression.

Immutable AI security/privacy and implementation reviews certify the candidate
against that manifest. They do not replace the repository owner's explicit
decision to disclose the candidate. Visibility must remain unchanged until that
decision is separately recorded.

## Non-Negotiable Blockers

The release is blocked if any in-scope journey depends on:

- Runtime AI as the source of truth for compliance decisions.
- Mutable submitted packages.
- Stakeholder-specific copies of the same invoice.
- Audit logging implemented only as application logs.
- Unapproved production configuration.
- Human-authority actions performed by system or AI actors.
- Missing provenance for submitted claimed amounts.

## Certification Record Template

Use this template for each release candidate:

```markdown
# Release Certification: <version>

## Decision

Certified | Certified with exceptions | Blocked

## Scope

- Pilot/customer scope:
- Included journeys:
- Excluded capabilities:

## Evidence

- Requirements trace:
- ADRs:
- Architecture updates:
- Test results:
- Journey results:
- Configuration versions:
- Provenance exports:
- Security/privacy review:
- AI evaluation:
- Operational runbooks:

## Exceptions

- Exception:
- Owner:
- Risk:
- Compensating control:
- Target resolution:

## Signoff

- Product:
- Engineering:
- Security/privacy:
- Release owner:
```

## SUB-50 Audit Timeline Gate

SUB-50 is eligible for approval only when the immutable PR diff proves a typed
GET-only audit contract, canonical submitted scope, exact actor/version/hash
evidence, both package trails, and zero-mutation Auditor denial. The clean
Compose suite must pass twice with identical semantic fingerprints. Passing
this gate satisfies the audit reconstruction precursor but does not replace
SUB-55 Playwright artifacts or release approval.

## SUB-26 Playwright Harness Gate

SUB-26 is eligible for approval only when an immutable PR diff and hosted CI
prove that a clean isolated Compose run completes Journey 11 through normal
login/logout for every persona without database edits, test endpoints, or role
switching. The evidence must retain JSON results, video, trace, lifecycle and
role screenshots, runtime logs, and Compose state; assert server-side forbidden
actions; and match captured distinct v1/v2 archive hashes in the final read-only
audit projection.

The same scenario must pass headless and in a paced headed mode. Passing this
gate certifies the harness and its integration into required CI. SUB-55 remains
the terminal release decision, and SUB-53 remains responsible for documented
operator-facing reproducible commands.

## SUB-53 Reproducible Operations Gate

SUB-53 is eligible for approval only when the immutable diff and executable
evidence prove a clean-checkout operator can validate prerequisites; start,
stop, migrate, seed/reset, and health-check the complete stack; independently
start API, worker, and web boundaries; and invoke headless and paced headed
Journey 11 without SQL or test-only state mutation.

The runbook must identify every synthetic-only default, prohibit real data and
credential reuse, record the local no-external-key extraction adapter, preserve
the worker/reset ordering, and retain deterministic fingerprints and browser
artifacts. Passing this gate unblocks SUB-55 but does not replace its terminal
release review.

## SUB-55 Terminal POC Release Gate

SUB-55 is certifiable only when its issue-scoped immutable PR diff and hosted
manifest prove all acceptance criteria against the exact candidate head. Every
persona must visibly show name, organization, role, bounded permissions, and
logout. The UI must execute configuration activation, upload/processing,
extraction correction, deterministic validation, attestation, package
generation, submission, Government return, NGO revision/resubmission, final
Government approval, and Auditor reconstruction.

The release evidence must also prove direct forbidden API commands fail
without mutation, retained validation/package inputs replay exactly, v1 remains
unchanged, v2 has distinct identities and bytes, and the Auditor has no
mutation surface. Both clean headless and default paced headed modes retain
machine results, video, trace, screenshots, HTML, logs, Compose state, exact
SHAs, commands, versions, counts, and hashes.

Applicable ADR/architecture, boundary, security/privacy, AI/configuration,
traceability, implementation, journey, and release AI reviews must all return
`Approved` against one immutable base/head diff. Human code review is not a
gate. This synthetic development POC may be `Certified` after merge and clean
post-merge verification; staging, production, real data, or a real-world
release promotion remains a separately human decision.

## SUB-78 Terminal MVP Release Gate

Current candidate decision: **Blocked** pending exact PR-head hosted checks,
the paced headed Journey 12 recording, eight immutable-diff AI approvals,
merge, and clean post-merge verification. The implementation and local
headless/two-pass evidence are complete; this pre-PR decision is not a defect
waiver or scope reduction.

The MVP becomes eligible for **Certified** only when the exact candidate proves
all five normal persona sessions, useful bounded landing pages, exact
configuration/profile context, supported English/Spanish profile intake,
changed/unknown safe routing, deterministic validation, distinct human
authority, immutable v1 and v2 packages, prospective successor activation, and
post-successor reconstruction of original configuration/profile references and
archive hashes.

Required retained evidence is static/unit/frontend/build output, two fresh-
volume Compose passes with an equal reset fingerprint, clean headless and
default 650 ms headed Journey 12 results, video, trace, screenshots, HTML,
runtime logs, Compose state, exact base/head/merge SHAs, commands, versions,
counts, and artifact hashes. Architecture/ADR, traceability, boundary,
security/privacy, AI/configuration, implementation, journey, and release AI
reviews must all approve the same immutable diff. Human code review is not a
gate.

Certification remains limited to the local/CI synthetic MVP. Hosted production,
real data, public write access, SSO/MFA, malware scanning, backup/legal hold/
retention, penetration testing, broader document classes, notifications, and
payment execution are excluded and require separately scoped decisions.
