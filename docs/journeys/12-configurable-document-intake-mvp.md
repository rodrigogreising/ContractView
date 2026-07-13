# Journey 12: Configurable Document-Intake MVP

Status: Build (`SUB-74` merged; `SUB-75` implementation active)

Controlling epic: `SUB-73`

Design gate: `SUB-74`

Terminal certification issue: `SUB-78`

Machine contract:
`docs/architecture/document-intake-mvp-policy.json`

## Purpose

Certify that ContractView turns narrow synthetic document support into a
governed, deterministic configuration capability without weakening the
certified role-based workflow. The journey must prove immutable profile
versions, safe changed/unknown-layout routing, exact historical references,
five useful role landing pages, server authority, and retained evidence from a
clean environment.

## Actors

- Configuration Administrator assigned to the synthetic agency and contract.
- NGO Preparer assigned to the synthetic nonprofit and contract.
- NGO Approver assigned to the same synthetic nonprofit and contract.
- Government Reviewer assigned to the synthetic agency and contract.
- Auditor explicitly assigned read-only access to the synthetic contract.
- System worker executing pinned local OCR and deterministic profile/rule jobs.

System and AI actors have no profile approval, configuration activation,
attestation, submission, return, approval, or audit-mutation authority.

## Preconditions

- A clean Docker Compose environment with fresh PostgreSQL and MinIO state.
- Closed synthetic catalogs and deterministic generators only.
- At least two English and two Spanish synthetic vendor-invoice fixtures for
  their respective supported profiles.
- A changed-layout fixture, an unknown-layout fixture, and a historical-replay
  fixture.
- Seeded server-issued credentials and canonical role/contract assignments for
  all five personas.
- No hosted model key, runtime LLM, customer data, real identity, or test-only
  role switch.
- The exact base configuration, profile fixture set, local OCR/parser, schema,
  mappings, rules, workflows, views, and templates are version identified.

## Workflow Path

### 1. Govern English and Spanish profile versions

1. The Configuration Administrator logs in normally and sees current identity,
   organization, role, contract scope, configuration/profile history, active
   versions, evaluation state, and next actions.
2. The administrator creates immutable draft profiles for English and Spanish
   synthetic vendor-invoice layouts using existing ontology contracts.
3. Testing freezes each candidate and evaluates its versioned fixture set.
4. Required normalized fields and source locations are 100% exact for all
   supported fixtures. A repeated run produces identical evidence hashes.
5. The assigned administrator approves the exact tested versions and activates
   a configuration bundle that names their exact profile ids and versions.
6. Direct draft-to-active, stale-version, cross-contract, and unassigned-admin
   commands are denied without mutation.

### 2. Process a supported English document

1. The NGO Preparer logs in normally and sees preparation status, next action,
   and exact active configuration/profile context.
2. The preparer uploads the supported English fixture through the normal UI.
3. The worker retains artifact hash, local OCR/parser versions, source
   locations, fingerprint specification/result, exact profile/configuration
   references, and `recognized_profile_draft`.
4. Draft fields remain subject to human review before canonical use.
5. Repeating identical declared inputs produces the same fingerprint and
   normalized draft or the same explicit deterministic failure.

### 3. Process a supported Spanish document

1. The NGO Preparer uploads a supported Spanish fixture through the normal UI.
2. The same evidence contract applies with the Spanish profile's exact id,
   version, and BCP 47 language tag.
3. The UI remains English; the source-document language does not grant a
   multilingual product claim.

### 4. Fail safe for changed and unknown layouts

1. The preparer uploads the changed-layout and unknown-layout fixtures.
2. Each produces `needs_profile_review`, retained artifact/OCR/fingerprint
   evidence, and no canonical expense, validation run, profile assignment, or
   activation event.
3. A noncanonical cluster suggestion is visible to the administrator but
   cannot assign a profile.
4. Administrator confirmation may create a Configuration-owned draft
   association only; it still requires test, approval, and bundle activation.

### 5. Complete the canonical human workflow

1. The NGO Approver logs in normally and sees the exact invoice,
   profile/configuration versions, validation freshness, blockers, and package
   readiness; only this actor attests and submits.
2. The Government Reviewer logs in normally and sees the submitted immutable
   version plus deterministic findings; only this actor returns or approves.
3. If returned, the NGO Preparer corrects the exact requested draft field, the
   NGO Approver separately revalidates/attests/resubmits, and the Government
   Reviewer approves v2.
4. Every persona logs out before the next persona logs in.

### 6. Activate a successor prospectively and reconstruct history

1. The Configuration Administrator tests, approves, and activates a successor
   profile/configuration version.
2. New intake resolves against the successor. Earlier invoice v1 and v2 keep
   the original exact profile/configuration references, validation results,
   package bytes/hashes, submissions, and decisions.
3. The Auditor logs in normally and reconstructs source-to-approval history,
   profile lifecycle, changed/unknown routing, human actors, immutable version
   references, and distinct package hashes without mutation authority.

## Expected Provenance Evidence

- Artifact ids, versions, hashes, object references, and source locations.
- OCR/parser and fingerprint specification versions plus deterministic
  fingerprints and cluster projection ids.
- Profile ids/versions, fixture-set versions, evaluation hashes, lifecycle
  actors/roles/timestamps/rationales, predecessor/successor, and exact active
  configuration-bundle references.
- Profile-match outcomes and human review/correction lineage.
- Immutable invoice snapshots, validation-input manifests, package reproduction
  manifests, submission/return/resubmission/approval events, and package hashes.
- Normal authenticated sessions and authorization denials for all five roles.
- Read-only audit projection joining declared immutable references, never
  command-side cross-capability SQL.

## Failure Modes

- A changed or unknown layout creates canonical invoice data.
- A cluster suggestion assigns or activates a profile automatically.
- Profile activation mutates a historical invoice, validation, package, or
  audit reconstruction.
- The browser, system, or AI actor performs a human-authority action.
- A hosted model, runtime LLM, external model credential, real identity, brand,
  or customer data enters the run.
- A profile bypasses `draft -> tested -> approved -> active -> superseded ->
  retired`, or test/approval evidence is mutable.
- A cross-tenant direct or indirect reference changes state.
- One persona retains a session during another persona's authority action.
- Role pages display invented state or become the authorization source.

## Certification Criteria

- All supported English/Spanish fixtures meet 100% expected field and source-
  location exactness; identical declared inputs reproduce fingerprints and
  normalized drafts.
- Changed and unknown fixtures route 100% to `needs_profile_review` with zero
  canonical mutation and zero automatic assignment.
- Configuration/profile lifecycle, exact activation references, human
  authority, tenant scope, and zero-mutation denials pass executable tests.
- All five role landing pages show identity, organization, role, exact context,
  bounded authority, next action, and normal login/logout with distinct
  server-issued sessions.
- Successor activation is prospective; retained evidence proves historical
  references and bytes are stable.
- A clean headless Playwright run passes and a paced headed run retains video,
  trace, screenshots, machine results, logs, hashes, and Compose metadata.
- Static, unit, integration, boundary, authorization, provenance,
  deterministic-replay, frontend, build, clean Compose, AI review, and release
  review gates approve the immutable merged diff.

## SUB-75 Configuration Checkpoint

Before profile execution begins in SUB-76, the existing reimbursement
configuration path proves the governance mechanics Journey 12 will reuse:

- a normal Configuration Administrator session reads the editable draft with a
  revision, saves through compare-and-update, tests that exact revision,
  approves the exact immutable evidence, and activates prospectively;
- stale save/test, wrong-role, unassigned, invalid-transition, and failed-test
  activation paths return without governed mutation;
- version list/detail exposes exact payload, payload hash, deterministic checks,
  result hash, human approval binding, lifecycle actor/role/rationale/time, and
  predecessor/successor evidence;
- diff and activation impact are hashed, replayable, noncanonical projections;
- historical invoice, validation, package, submission, snapshot, and audit-event
  references continue to resolve the original configuration after a successor
  activates; and
- the bounded administrator UI consumes generated DTOs and explains draft
  revision, deterministic evidence, diff, prospective impact, and historical
  references. SUB-77 remains responsible for the complete profile workspace.

This checkpoint does not claim English/Spanish profile fixtures, deterministic
profile matching, changed/unknown routing, or five-role Journey 12 completion;
those remain SUB-76 through SUB-78 acceptance criteria.

## SUB-76 Deterministic Intake Checkpoint

The executable backend now proves the Journey 12 profile and routing portion:

- immutable English and Spanish profile definitions each have two supported
  deterministic fixtures plus shared changed/unknown negative fixtures;
- pinned local `tesseract-5.5.0-eng+spa` and the versioned parser produce exact
  normalized fields and source lines for real English and Spanish PDFs;
- identical declared inputs reproduce fingerprints, normalized drafts, match
  results, and content hashes;
- changed and unknown layouts return `needs_profile_review`, retain artifact,
  raw OCR, fingerprint, match, and noncanonical cluster evidence, and create no
  fields, canonical expense, validation run, assignment, or activation;
- administrator confirmation creates a draft association only, while exact
  test evidence and human approval remain prerequisites for prospective profile
  activation; and
- a tested and approved configuration rollback can reactivate an exact
  historical profile reference through a new append-only rollback-activation
  event; and
- validation manifests retain the exact profile, configuration, fingerprint,
  OCR, parser, and artifact references used by recognized drafts.

This checkpoint does not claim the complete administrator workspace or the
five-role browser journey. Those remain SUB-77 and SUB-78.
