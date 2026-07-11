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
