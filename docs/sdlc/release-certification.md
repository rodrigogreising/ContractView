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
