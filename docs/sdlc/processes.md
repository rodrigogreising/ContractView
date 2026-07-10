# SDLC Processes

Each process below is a first-class project requirement. Implementation work should not bypass these gates when the affected capability is in scope.

## Process Matrix

| Process | Owner role | Trigger | Required artifact | Completion criterion |
| --- | --- | --- | --- | --- |
| Product intake and discovery | Product lead | New workflow, stakeholder need, pilot request, or major feature idea. | Problem statement, impacted stakeholders, success metric, in/out of scope. | Scope is clear enough to map to requirements and journeys. |
| Requirements traceability | Product lead plus engineering lead | Any major feature, workflow change, or release planning cycle. | Trace from requirement to ADR pillar, service boundary, journey, and release criterion. | No major feature lacks architectural and journey coverage. |
| ADR creation and review | Engineering lead | Material architecture decision, new service/package, persistence model change, AI authority change, or compliance boundary change. | New ADR or amendment under `docs/adr/`. | Decision is accepted, superseded, or explicitly rejected before implementation proceeds. |
| Architecture review | Engineering lead | New service, package, data owner, integration, or cross-service dependency. | Updated architecture docs and boundary checklist. | Ownership, dependencies, events, data ownership, and prohibited responsibilities are documented. |
| Threat modeling and privacy review | Security/privacy owner | New sensitive data flow, upload type, integration, support access path, export, or retention/deletion behavior. | Threat model, data classification, mitigation list, retention decision. | Risks are accepted or mitigated before release certification. |
| AI evaluation and model/prompt governance | AI owner plus domain reviewer | New or changed AI extraction, classification, summary, mapping, schema, or rule suggestion behavior. | Evaluation plan, model/prompt/parser version, sample set, quality metrics, human-review rules. | AI behavior is traceable and cannot create unreviewed compliance authority. |
| Deterministic rule/configuration certification | Rule/config owner | New or changed schema, mapping, rule, workflow, view, template, or configuration bundle. | Test cases, activation approval, version record, rollback/supersession path. | Configuration is draft, tested, approved, active, superseded, or retired as appropriate. |
| End-to-end journey certification | QA/release owner | Before every certified release and after material workflow changes. | Executed journey evidence from `docs/journeys/`. | MVP-critical journeys pass or have signed exceptions. |
| Release readiness review | Release owner | Candidate version is ready for release. | Release certification checklist, known risks, test results, journey evidence, ADR links. | Release is approved, blocked, or released with explicit exceptions. |
| Incident response and postmortems | Operations owner | Production incident, data-integrity concern, audit evidence gap, security event, or material integration failure. | Incident record, timeline, impact, root cause, corrective actions. | Corrective actions are tracked and relevant docs/tests are updated. |
| Audit evidence retention | Compliance owner | New evidence type, retention rule, deletion request, legal hold, or audit export path. | Evidence inventory, retention policy, deletion/tombstone behavior, legal hold rules. | Evidence needed for certified journeys remains reconstructable within policy. |

## Requirements Traceability

Every major feature must map to:

- ADR pillar.
- Functional or nonfunctional requirement.
- Owning service/package boundary.
- Certifiable journey.
- Release certification criterion.

Traceability may live in issue descriptions, release checklists, or dedicated traceability docs, but it must be reviewable during release certification.

## Architecture Governance

Material changes require an ADR or ADR amendment when they affect:

- Service/package boundaries.
- Canonical domain model.
- Provenance/event model.
- Configuration lifecycle.
- Validation determinism.
- Human authority over workflow.
- Sensitive data handling.
- AI responsibility boundaries.

## Boundary Review

Every new service or package must declare:

- Owner role.
- Responsibilities.
- Data owned.
- Allowed dependencies.
- Events emitted.
- Configuration consumed.
- Deterministic behavior required.
- Human authority boundary.
- Prohibited responsibilities.

## Journey Certification

Journey certification must prove both user-visible behavior and evidence quality.

Required evidence:

- Version under test.
- Fixture users, organizations, contract, budget, artifacts, and configuration bundle.
- Executed workflow path.
- Validation run ids.
- Artifact and package hashes where applicable.
- Event ids or exported event references.
- Known exceptions and signoff.

## Configuration Governance

Schemas, mappings, rules, workflows, views, templates, and configuration bundles must follow:

1. Draft.
2. Tested.
3. Approved.
4. Active.
5. Superseded.
6. Retired.

Production activation requires authorized approval, test evidence, activation timestamp, affected contract scope, and supersession/rollback path.

## Provenance Verification

Releases must prove:

- Immutable artifact references.
- Append-only material events.
- Validation-run version records.
- Field-level lineage.
- Package-generation manifests.
- Human authority events.
- Audit reconstruction for certified journeys.

## AI Governance

AI-assisted features must document:

- Intended use.
- Prohibited authority.
- Source evidence requirements.
- Model, prompt, parser, and evaluation versions.
- Confidence and review thresholds.
- Human correction path.
- Privacy and tenant-data controls.

AI must not be the unreviewed source of truth for submission-blocking validation, approvals, waivers, attestations, finalization, or historical validation reproduction.

## Security And Privacy Review

Security/privacy review is required for:

- Payroll, bank, tax, employee, vendor, and client-adjacent data.
- Upload, export, integration, retention, deletion, and support-access paths.
- Region or state-hosting commitments.
- Audit export and legal hold behavior.

## Operational Readiness

Before production use, in-scope operational surfaces need runbooks for:

- Background jobs.
- Queues and retries.
- Dead-letter handling.
- Integration failures.
- Support impersonation or delegated access.
- Audit export.
- Incident response.
- Backup, restore, and retention/deletion behavior.

## Release Evidence

Each certified version should link:

- Journey results.
- Test results.
- ADRs and architecture changes.
- Configuration migrations or activation records.
- Security/privacy reviews.
- AI evaluation evidence.
- Known risks and accepted exceptions.
