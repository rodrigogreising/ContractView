# ContractView Synthetic POC Runbook

Status: SUB-53 implementation evidence; local synthetic POC only

## Scope And Safety Boundary

This runbook operates the local Docker Compose proof of concept. Every included
identity, organization, transaction, document, credential, and package is a
synthetic fixture. Do not supply customer, employer, vendor, employee, account,
payment, or other real data. These commands do not authorize hosted deployment,
production use, external providers, or payment execution.

The active extraction adapter is local Tesseract plus the versioned fixture
parser. It needs no external OCR/LLM API key and sends no artifact bytes to a
third party. The Compose defaults below are public demo credentials, not
secrets, and must never be reused outside this isolated POC:

| Surface | Synthetic-only default |
| --- | --- |
| PostgreSQL database/user/password | `contractview` / `contractview` / `contractview` |
| MinIO access/secret | `contractview` / `contractview-demo-secret` |
| Session signing value | `local-synthetic-poc-only` |
| Persona credentials | `packages/test-fixtures/scenario.json` |

## Prerequisites

- Docker Engine or Docker Desktop with Docker Compose v2 and support for
  `docker compose up --wait` and Compose override tags.
- Python 3.12.x; CI uses the exact version in `.python-version`.
- Node 20.19 or newer and below 21; CI uses the exact version in `.nvmrc`.
- `curl`, enough free space for the pinned images, and ports 4173, 5432, 8000,
  9000, and 9001 available for the normal local stack.
- A Chromium-capable desktop session for headed recording. The runner installs
  its pinned Playwright Chromium build.

From the repository root, validate the prerequisites:

```bash
nvm use
make prerequisites
```

If a different Node version is active, prerequisite validation stops before
starting or changing Compose state.

## Normal Runtime

The following commands are equivalent to `bash scripts/poc.sh <command>` and
all fail on the first unsuccessful operation.

| Operation | Command | Result |
| --- | --- | --- |
| Start complete stack | `make start` | Builds and waits for PostgreSQL, MinIO, API, worker, and web; then checks health. |
| Stop, preserve data | `make stop` | Stops Compose and keeps named volumes. |
| Follow logs | `make logs` | Follows all service logs. |
| Show state | `make status` | Shows Compose service state. |
| Start API boundary | `make api` | Starts PostgreSQL, MinIO, and API. |
| Start worker boundary | `make worker` | Starts worker and required API dependencies. |
| Start web boundary | `make web` | Starts web and required API dependencies. |
| Apply migrations | `make migrate` | Applies numbered migrations through `app.manage`. |
| Idempotent seed | `make seed` | Seeds the closed synthetic catalog through `app.manage`. |
| Safe deterministic reset | `make reset` | Stops worker, resets database/object storage, restarts worker, and prints the state fingerprint. |
| Verify readiness | `make health` | Checks API, worker, and web readiness. |

The normal endpoints are:

- Web: `http://localhost:4173`
- API readiness: `http://localhost:8000/health/ready`
- MinIO API/console: `http://localhost:9000` / `http://localhost:9001`

For an isolated concurrent stack, set `COMPOSE_PROJECT_NAME`, `POSTGRES_PORT`,
`MINIO_PORT`, `MINIO_CONSOLE_PORT`, `API_PORT`, and `WEB_PORT`. The health
command honors the API and web overrides.

Reset never requires SQL. It deliberately stops the worker before replacing
the schema, preventing heartbeat/job polling from racing the reset. It clears
the synthetic object bucket, applies numbered migrations, idempotently seeds
the fixture catalog, restarts the worker, and prints the canonical fingerprint.
For two independent fresh-volume proofs, run:

```bash
CI_PROJECT_NAME=contractview-hermetic-local \
  bash scripts/ci/run_hermetic.sh artifacts/hermetic
```

## Canonical Journey 11 Commands

Headless certification starts a uniquely named isolated Compose project,
replaces its volumes, resets through the supported command, starts the real
worker, completes all five persona sessions, and retains JSON, video, trace,
screenshots, HTML, runtime logs, and Compose state:

```bash
make journey11-headless
```

Paced headed recording executes the same scenario. Its default slow motion is
650 milliseconds between browser actions:

```bash
make journey11-headed
```

The npm aliases are `npm run journey11:headless` and
`npm run journey11:headed`. To choose an evidence directory explicitly:

```bash
bash scripts/poc.sh certify-headless artifacts/journey11/headless
bash scripts/poc.sh record-headed artifacts/journey11/headed
```

Set `JOURNEY11_SLOW_MO_MS` only to change headed pacing. Set
`JOURNEY11_KEEP_RUNTIME=true` only for local diagnosis; the default removes the
isolated runtime and volumes after retaining evidence.

## Recovery And Failure Evidence

- A failed Journey 11 run still retains browser failure context, trace, video,
  screenshots, Compose service state, and runtime logs in its chosen directory.
- A failed hermetic pass retains service logs and Compose state for that pass.
- Inspect with `make status` and `make logs`; rerun `make health` after a repair.
- Use `make reset` for supported synthetic recovery. Do not edit the database,
  object store, session storage, or role state manually.
- Submitted packages and provenance are evidence. Reset is permitted only for
  the disposable local synthetic environment and must never be framed as a
  production retention/deletion mechanism.

SUB-55 owns the final release certification and canonical retained recording.
This runbook supplies its reproducible operator commands but does not itself
authorize production promotion.
