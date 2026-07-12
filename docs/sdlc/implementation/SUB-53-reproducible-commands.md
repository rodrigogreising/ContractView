# SUB-53 Implementation Evidence: Reproducible POC Commands

Status: Implementation complete; immutable PR review pending

## Scope And Decision

SUB-53 provides one fail-fast operator contract at `scripts/poc.sh`, with Make
and npm aliases and a synthetic-only runbook. It covers prerequisites,
start/stop, migrations, idempotent seed, safe deterministic reset, independent
API/worker/web startup, health/status/logs, headless certification, and paced
headed recording. The runbook names the POC developer/release operator, command
triggers, detection signals, mitigation, supported recovery, evidence, and
Linear corrective-action handoff.

No ADR is required. The script is an operations adapter over the existing
Compose topology and supported `app.manage` commands. It owns no domain data,
service, package, table, lifecycle decision, AI behavior, or human authority.
Published ports are parameterized for concurrent isolated projects without
changing container/network boundaries.

## Safety And Determinism

- Reset stops the worker before schema/object-store replacement and restarts it
  afterward, preventing heartbeat or job polling from racing the reset.
- Reset applies numbered migrations, idempotently seeds the closed synthetic
  catalog, and prints the canonical state fingerprint. No SQL or test endpoint
  is part of the operator interface.
- Prerequisite validation fails before Docker mutation when Python/Node do not
  meet the supported ranges. Docker Compose v2 and `curl` are required.
- Local PostgreSQL, MinIO, session, and persona defaults are explicitly public
  synthetic demo credentials. The local extraction adapter requires no external
  provider key and sends no bytes to a third party.
- Stop preserves named volumes. Clean certification commands create and remove
  their own volumes while retaining evidence artifacts.

## Executable Evidence

- Static gate: 78 repository tests and 23 frontend tests/build passed.
- Shell contract: `bash -n scripts/poc.sh` and the executable help/Make/npm
  delegation tests pass.
- Fail-fast toolchain evidence: Node 20.15 was rejected before Compose mutation;
  repository-pinned Node 20.20.2 and Python 3.12.2 passed.
- Isolated normal stack: `start` built/waited for PostgreSQL, MinIO, API,
  worker, and web on non-default ports; API/worker/web health passed.
- `migrate`, `seed`, `reset`, and `health` passed through the public operator
  contract. Two safe resets printed the same fingerprint:
  `7a4690eb63c89aba73fdee2a93f1a4e18737468e965a56ee9dedfb8691d590fb`.
- `stop` removed containers/network and preserved the isolated named volumes.
- `make journey11-headless`: one clean browser test passed in 10.8 seconds;
  retained video SHA-256
  `f234d1422f8a0d177d85c9772218268598e970cb9f8986193dc3e45e6265ba33`
  and trace SHA-256
  `980aa5a90e72b035a58220a8f88615f8548785d937b1c1a8f1b376ec1fd89a79`.
- `make journey11-headed`: the default 650 ms paced scenario passed in 1.0
  minute; retained video SHA-256
  `d65ce0bb7e063c4e8ff3943123cbe5d5f2ba425663f91ce1d15f3a9579e58538`
  and trace SHA-256
  `f1a4f86c4836aab9c198c93c5e4e070bedaaf11b3a8777a40e763ac3d1375761`.

The issue PR must additionally retain hosted static, two-pass hermetic Compose,
headless Journey 11, and schema-valid manifest evidence before immutable AI
review.

## Release Impact

Passing SUB-53 supplies the reproducible clean-checkout operator commands and
unblocks SUB-55. It does not itself make a terminal release decision or permit
real data, external providers, hosted deployment, or production retention.
