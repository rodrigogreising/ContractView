# SUB-61 Executable Ontology And Shared Contracts Evidence

Status: Build

## Control

- Issue: `SUB-61` / REC-05
- Branch: `codex/sub-61-executable-ontology`
- Base SHA: `8e7ad3644f847985833f3a524988b97451d391fe`
- Project: ContractView / Build
- Generation skills: ADR/architecture, boundary, requirements traceability,
  implementation/tests
- Required AI reviews: ADR/architecture, boundary, requirements traceability,
  implementation/tests
- Human approval: not required; no production configuration or authority
  action is performed.

## Contract Surface

- `domain-types`: artifacts, typed fields, entities, relations, roles,
  resources, actions, lifecycles, reason codes, and version references.
- `rule-contracts`: deterministic rules, severity/outcome, results, and
  validation runs.
- `event-contracts`: material event names and actor/aggregate/version envelope.
- `configuration-contracts`: workflow, view, template, bundle, test-evidence,
  approval, predecessor, and rollback references.

All registries are version `1.0.0`. Every contract field's type, collection
shape, requiredness, nullability, default, and constraint is defined in the
registry. The generator contains no parallel model declarations. The
dependency graph is acyclic. A minor version may add optional fields;
closed-vocabulary changes, removals, required-field changes, or
type/default/constraint/semantic changes require a major version and
coordinated consumer migration.

## Generated Consumers

`scripts/generate_shared_contracts.py` deterministically generates:

- `services/api-workflow/app/shared_contracts.py` with Pydantic contracts and
  runtime enums;
- `apps/web-app/src/generated/contracts.ts` with matching TypeScript unions,
  interfaces, and DTOs.

Python authorization consumes generated roles, resources, and actions.
Provenance consumes generated event vocabulary. Authentication and active
configuration responses validate through generated DTOs. React consumes
generated identity, active-configuration, and validation DTOs; REC-10 migrates
the remaining feature-local DTOs while decomposing the app.

The identity DTO retains the existing `organizationId` field. Both Python and
TypeScript consumer tests make that additive public API compatibility explicit,
so regeneration cannot silently narrow the authenticated identity response.

## Executable Evidence

- Generator freshness: 4 registries and 2 consumers pass.
- Registry validator: 18 contracts, typed field references, semantic and
  dependency versions, lifecycle parity, unique closed vocabularies, and
  acyclic dependencies pass.
- Five policy/compatibility tests prove optional additions pass while closed
  vocabulary and field-type changes fail; renderer checks prove optional and
  required TypeScript fields follow canonical definitions.
- Six pure Python Pydantic tests validate requiredness parity, round trips,
  hashes, unknown-field/vocabulary rejection, bundles, events, views,
  templates, rules, entities, relations, and the existing identity response.
- Local TypeScript evidence: 2 files / 12 tests pass; `tsc` and Vite build pass.
- The local Node 20.15 runtime emits Vite's Node >=20.19 warning but exits zero;
  REC-11 owns version pinning. The containerized build uses the repository's
  Node 20 image and passes.
- Corrected clean-container evidence for the required-fix head explicitly
  rebuilt `api` and `web-test` before execution: 157 API tests and 12 frontend
  tests pass after a deterministic reset.
- All five Compose services are healthy. A real auditor login, identity lookup,
  and logout pass against the rebuilt API, and both identity responses retain
  `organizationId=org-oversight`.

An earlier 150/9 run was discarded because a mistyped service name prevented
the new test images from being built. Those stale-image counts are not used as
certification evidence.

The first required-fix run produced 156 passes and one failure because the
existing validation-boundary test rejected any source occurrence of the word
`model`, including Pydantic's `model_dump`. The test now inspects imported
modules through the Python AST and continues to forbid extraction and AI
provider dependencies without rejecting ordinary domain models. The final
rebuilt run is the 157/12 result above.

## Remaining Required Evidence

Updated immutable artifact hashes and manifest, final review of the required-fix
head, merge SHA, and post-merge verification are pending. The issue must not
move to Done until those checks complete.
