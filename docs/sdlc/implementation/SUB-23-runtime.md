# SUB-23 Implementation Evidence: POC Runtime

Status: Implemented and verified

## Scope

- React/TypeScript web application.
- FastAPI API and Python worker.
- PostgreSQL canonical store and MinIO artifact store.
- Docker Compose health and dependency orchestration.
- Deterministic SQL migrations and seed/reset commands.

## Boundary Notes

The runtime follows ADR 0002. API and worker share the modular-monolith application package but run as separate processes. Initial seed data contains only a fixture version marker and never injects completed workflow state.

## Verification

- `docker compose config --quiet`: passed.
- Docker API, worker, and web images: built successfully.
- Frontend dependency audit: 0 vulnerabilities.
- Clean `docker compose down -v` then `up -d`: passed.
- PostgreSQL, MinIO, API, worker, and web health checks: all healthy.
- API readiness reported database and object storage ready.
- Destructive synthetic reset recreated the schema, cleared artifact storage, reran migrations, and seeded `fixture_version=poc-v1`.
- Containerized Pytest: 1 passed.
- Containerized Vitest: 1 passed.
- Python compileall and `git diff --check`: passed.

## Review

Decision: Approved.

All SUB-23 acceptance criteria are evidenced. The runtime contains no test-only final-state injection; the seed is limited to a fixture-version marker for later synthetic fixture work.
