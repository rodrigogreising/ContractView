# SUB-62 Module Ownership And Capability Persistence Evidence

Status: Build

## Control

- Issue: `SUB-62` / REC-07
- Branch: `codex/sub-62-module-ownership`
- Base SHA: `1cc5d9a78060a0c40bb67cb8770d0c7de2f53639`
- Project: ContractView / Build
- Generation skills: ADR/architecture, boundary, requirements traceability,
  implementation/tests
- Required AI reviews: ADR/architecture, boundary, requirements traceability,
  implementation/tests
- Human approval: not required; this change performs no production promotion
  or human-authority action.

## Physical Layers

| Layer | Physical implementation |
| --- | --- |
| Domain | `app/domain` generated contracts and authorization invariants |
| Application | 19 modules in `app/application/commands` plus application-owned ports/providers |
| Persistence | `app/adapters/persistence` PostgreSQL repositories, catalog, and transaction adapter |
| Integration | `app/adapters/object_storage`, `app/adapters/extraction`, runtime health, and `app/integration` composition |
| Worker | `app/worker_runtime` polling and health; `app.worker*` are thin composition wrappers |
| HTTP | `app/http/api.py`; `app.main` is a thin composition wrapper |

Flat application module names remain compatibility exports for the existing
test/API import surface. They contain no implementation or SQL.

## Persistence Ownership

`module-ownership-policy.json` assigns 39 physical tables exactly once across
identity, configuration, artifacts, extraction, invoices, validation,
packages, workflow, provenance, and platform bootstrap. The persistence
catalog contains 149 named statements. Each entry records:

- owner and consuming capability;
- operation and read/write tables;
- all source owners;
- owner repository, application query/command port, or declared-read-model
  collaboration.

The application unit-of-work exposes one repository per capability and a
read-model repository. The PostgreSQL adapter accepts only generated
`Statement` identifiers, rejects inline SQL and foreign-owner execution, and
does not expose its raw connection. The former submitted-artifact multi-owner
update was split into a read projection and artifact-owned update.

## Non-Persistence Adapters

MinIO artifact bytes, runtime health, Tesseract execution, Argon2 password
verification, OpenPyXL workbook parsing, and ReportLab PDF rendering are behind
application-owned ports. Application commands no longer import their provider
packages, PostgreSQL, settings, runtime composition, or subprocess execution.
Tesseract remains the single real replaceable extraction adapter; this refactor
changes placement, not AI authority.

Package generation is explicitly split: the workflow application coordinator
checks attestation and authority, while the Packages capability owns package
persistence and deterministic rendering. This prevents a circular capability
implementation dependency without transferring canonical package ownership to
workflow.

## Executable Evidence

- Persistence statement validator: 149 named statements, no inline application
  SQL, no unused IDs, SQL-derived read/write tables matching catalog metadata,
  no unowned table references, no multi-owner writes, and no owner/table
  mismatch. Every use must match its declared consumer capability and valid
  repository/query-port/command-port/read-model semantics.
- Module validator: six layer directions, 39 table owners, all migration tables
  owned, no application/domain infrastructure imports, and declared capability
  dependencies only.
- Negative policy tests cover application-to-persistence imports, HTTP
  persistence imports, multi-owner writes, and owner/table mismatch.
- Runtime repository tests cover inline SQL rejection, wrong-owner rejection,
  read-model isolation, repository exposure, explicit commit, default rollback,
  exception rollback, connection closure, and one owner per write statement.
- Clean-volume Compose certification passed after destroying PostgreSQL and
  MinIO volumes, rebuilding the API and frontend test images, applying the
  deterministic reset, and starting the complete runtime.
- The reset-state API regression passes 165 tests; the containerized frontend
  regression passes 12 tests; the production TypeScript/Vite build passes; and
  all five API, worker, web, PostgreSQL, and MinIO services report healthy.
- A real server-issued auditor session passed readiness, login, `/auth/me`, and
  logout with the seeded `org-oversight` identity preserved.
- The 46 repository policy tests pass, including negative dependency,
  persistence-owner, statement-drift, and transaction-boundary cases.
- The full API suite is clean-reset deterministic but is not independently
  isolated per test: an immediate second run against its mutated database does
  not pass. REC-11 owns hermetic per-run CI state; SUB-62 certification therefore
  requires the documented reset or clean-volume precondition.
- Artifact hashes, immutable AI reviews, merge, and clean post-merge
  verification remain required before Done.
