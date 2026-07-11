# Codex Playbooks

This repo uses documentation as an operating system for future implementation work. Codex agents should inspect these docs before making architecture, implementation, testing, or release changes.

## Default Read Order

Before material work, read:

1. `solution_requirements.md`
2. `docs/adr/0001-core-architectural-pillars.md`
3. Relevant files in `docs/architecture/`
4. Relevant journey specs in `docs/journeys/`
5. Relevant SDLC gates in `docs/sdlc/`

## Architecture Cartographer

Use this playbook when a change affects system shape, service/package ownership, data flow, or runtime responsibilities.

Codex should:

- Identify the affected ADR pillar.
- Update service/package maps when a new unit or dependency is introduced.
- Keep the map declarative until implementation frameworks are selected.
- Check that ownership of canonical invoice state, configuration, validation, provenance, artifacts, and reporting remains clear.
- Avoid documenting customer-specific code paths as the default solution.

Output should include:

- Updated architecture docs.
- Any ADR change needed.
- A short explanation of changed ownership or dependencies.

## Boundary Guardian

Use this playbook when implementation work adds a service, package, dependency, API, event, job, or data owner.

Codex should verify:

- The owning unit is named.
- Allowed dependencies are explicit.
- Prohibited responsibilities are not violated.
- Reporting projections do not become canonical state.
- UI behavior does not replace server-side permission checks.
- AI-assisted behavior does not perform compliance-critical authority.

Blockers to flag:

- Runtime AI as compliance source of truth.
- Mutable submitted packages.
- Stakeholder-specific invoice copies.
- Audit evidence stored only in application logs.
- Workflow transition without permissioned human/system actor semantics.

## Journey Certifier

Use this playbook when changing user workflows, validation, package generation, issue handling, submission, review, approval, payment status, or audit surfaces.

Codex should:

- Map the change to one or more journey specs in `docs/journeys/`.
- Add or update journey criteria when a new certifiable behavior appears.
- Ensure each journey has actors, preconditions, workflow path, provenance evidence, failure modes, and certification criteria.
- Preserve multi-user semantics across nonprofit, agency, support/admin, auditor, and system actors.

Output should include:

- Updated journey specs.
- Test scenarios or acceptance criteria tied to journey certification.

## Provenance Auditor

Use this playbook when a change affects artifacts, fields, invoice lines, validation, correction, submission, returns, approvals, payment status, or audit export.

Codex should verify that the design records:

- Immutable artifact references.
- Artifact and package hashes.
- Field-level source locations.
- Parser/model/importer versions.
- Mapping, schema, rule, workflow, template, and configuration bundle versions.
- Append-only material events.
- Human correction, waiver, accepted-risk, attestation, return, approval, and finalization events.
- Reconstruction path from claimed amount to submitted package and decision history.

If provenance is missing, treat it as a product defect, not a logging enhancement.

## Rule/Config Reviewer

Use this playbook when work touches schemas, mappings, rules, workflows, views, templates, or configuration bundles.

Codex should verify:

- Configuration follows draft, tested, approved, active, superseded, retired lifecycle.
- Production activation has authorized approval and test evidence.
- Historical submitted invoices retain original configuration versions.
- Re-validation creates a new validation run rather than overwriting old results.
- AI-generated configuration is reviewed, tested, approved, and versioned before production use.

Required framing:

- Deterministic software runs compliance-critical checks.
- AI may suggest configuration but does not become runtime compliance authority.

## Release Certifier

Use this playbook when preparing release notes, certification evidence, test plans, or production readiness reviews.

Codex should assemble:

- Requirements-to-ADR trace.
- Requirements-to-journey trace.
- Architecture changes and ADR links.
- Test and journey certification evidence.
- Configuration versions and activation records.
- Provenance exports or reconstruction evidence.
- Security/privacy review evidence.
- AI evaluation evidence where applicable.
- Operational runbooks and known risks.

Release decision must be one of:

- Certified.
- Certified with exceptions.
- Blocked.

## Immutable Change Reviewer

Use `docs/codex/review-preflight.md` before every ContractView review skill.

Codex should:

- verify the Linear issue, project stage, PR URL, base/head SHA, declared scope, and evidence manifest;
- review the complete immutable diff without editing during the review pass;
- block unscoped, dirty, default-branch, prose-only, or unmerged-prerequisite work;
- require high-risk work to retain fresh-context or explicit human review evidence;
- require merge SHA and clean post-merge verification before Linear `Done`.

## Documentation Update Rules

- Keep docs ASCII unless existing content requires otherwise.
- Prefer architecture-level language until implementation framework decisions are made.
- Add ADRs for material architecture decisions rather than hiding decisions in process docs.
- Keep journey specs testable and evidence-oriented.
- Update SDLC gates when a new class of release evidence becomes necessary.

## Quick Checks

Before closing a material change, run targeted searches for risky framing:

```sh
rg -n "runtime AI.*source of truth|mutable submitted|stakeholder-specific copies|application logs only|unapproved production configuration" docs solution_requirements.md
```

Then verify:

- Every affected ADR pillar is represented.
- Every affected MVP capability maps to a service/package boundary.
- Every affected journey has certification criteria.
- Every new SDLC process has owner role, trigger, artifact, and completion criterion.
