# SUB-59 Modular-Monolith Architecture Evidence

Status: In Progress

## Decision

SUB-59 amends ADR 0002 and makes the ContractView POC architecture
decision-complete as one enforceable modular monolith. The readable contract is
`docs/architecture/modular-monolith.md`; the machine contract is
`docs/architecture/modular-monolith-policy.json`.

## Issue Boundary

- Branch: `codex/sub-59-rec-02-modular-monolith`
- Base SHA: `27a308678fb6ce7420e491bc63eaf9beb959bdd6`
- Project stage: `Design Review`
- Generation skills: `cv-generate-adr-architecture`,
  `cv-generate-boundary-review`, and
  `cv-generate-requirements-traceability`
- Required AI reviews: `cv-review-adr-architecture`,
  `cv-review-boundary-review`, and
  `cv-review-requirements-traceability`
- Human code review: not required.
- Runtime behavior: unchanged by this architecture issue.

## Architecture Coverage

The decision defines:

- domain, application, persistence, integration, worker, and HTTP layers;
- inward dependencies and integration-owned composition;
- unique owners for identity, configuration, artifacts, extraction, invoices,
  validation, packages, workflow, and provenance;
- application command/query ports, immutable snapshots, versioned events, and
  declared read models as collaboration mechanisms;
- application-owned repository and unit-of-work ports;
- capability-owned tables, repositories, migrations, and transaction access;
- prohibition of cross-capability SQL, command joins, writes, shared mutable ORM
  models, and database-connection escape hatches;
- executable ontology and closed vocabulary;
- strict configuration-definition versus runtime-evidence separation;
- future service-extraction seams without adding network services to the POC.

## Current-State Findings

SUB-59 deliberately records nonconformance instead of treating documentation as
implementation proof:

- 22 files under `services/api-workflow/app` execute SQL directly.
- The current directory is flat and does not separate the six layers.
- `services/api-workflow/app/main.py` is 262 lines and combines route wiring with
  runtime composition concerns.
- Domain, rule, event, and configuration packages are README placeholders.
- Existing command modules contain cross-owner reads/writes that REC-07 must
  replace with owner repositories and application ports.

REC-05 owns executable contracts. REC-07 owns the physical module/persistence
refactor and forbidden-import/table-ownership tests. REC-12 must reconcile
prior completion claims and recertify the boundary evidence.

## Certification

`python3 scripts/check_architecture_policy.py` validates the repository policy
and required evidence links. `python3 -m unittest
scripts.tests.test_architecture_policy -v` proves fail-closed behavior for layer
inversion, duplicate ownership, cross-capability SQL, missing capabilities,
dependency cycles, configuration/runtime overlap, unknown vocabulary, and
future shared tables. Thirteen tests also cover closed vocabularies, exact
version references, prospective activation, and prevention of extra POC network
services.

Exact commands, versions, counts, hashes, immutable PR SHAs, AI review
decisions, merge SHA, and clean post-merge results are recorded in the
machine-readable issue manifest and Linear handoff comments.

The traceability review required an explicit release-criterion column. The
follow-up commit maps every recovery architecture requirement to named gates in
`docs/sdlc/release-certification.md`, and the policy validator now requires the
column.
