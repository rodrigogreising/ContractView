# SDLC Operating Model

ContractView's software developer lifecycle must support regulated, cross-organizational reimbursement workflows. The goal is not only to ship features; each release must be certifiable against provenance, deterministic validation, configuration governance, human authority, security, privacy, and operational readiness expectations.

## Lifecycle Stages

1. Product intake and discovery.
2. Requirements traceability.
3. Architecture and ADR review.
4. Service/package boundary review.
5. Security, privacy, and data-governance review.
6. AI evaluation and configuration governance review where applicable.
7. Implementation and tests.
8. End-to-end journey certification.
9. Release readiness and evidence signoff.
10. Production operation, incident response, and postmortems.

## Release Gate Summary

Each releasable version must show:

- Requirements map to ADR pillars and certifiable journeys.
- Material architecture changes have ADR coverage.
- Service/package ownership and dependencies are documented.
- Deterministic validation and configuration behavior have test evidence.
- Provenance evidence exists for certified journeys.
- Sensitive data flows have security/privacy review.
- AI-assisted behavior has model/prompt/parser versioning and human-review controls.
- Operational runbooks exist for background jobs, integrations, support access, audit export, and incident response where those capabilities are in scope.

## Required Evidence Locations

| Evidence | Expected location |
| --- | --- |
| Product and solution requirements | `solution_requirements.md` |
| Architectural decisions | `docs/adr/` |
| Service/package map | `docs/architecture/` |
| Journey specs | `docs/journeys/` |
| SDLC process definitions | `docs/sdlc/processes.md` |
| Linear workflow states and labels | `docs/sdlc/linear-workflow.md` |
| Release certification criteria | `docs/sdlc/release-certification.md` |
| Codex operating playbooks | `docs/codex/playbooks.md` |

## Certification Philosophy

A version is not ready merely because unit tests pass. A version is ready when the team can demonstrate that it performs the reimbursement job end to end, preserves evidence, enforces the correct authority boundaries, and can explain historical results.
