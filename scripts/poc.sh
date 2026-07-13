#!/usr/bin/env bash
set -euo pipefail

compose=(docker compose)

usage() {
  cat <<'EOF'
Usage: bash scripts/poc.sh <command> [artifact-directory]

Commands:
  prerequisites     Validate the local POC toolchain.
  start             Build and start PostgreSQL, MinIO, API, worker, and web.
  stop              Stop the POC while preserving named volumes.
  migrate           Start dependencies and apply numbered migrations.
  seed              Start dependencies and idempotently seed synthetic data.
  reset             Safely reset synthetic state and print its fingerprint.
  api               Start PostgreSQL, MinIO, and the API.
  worker            Start the API dependencies and worker.
  web               Start the API dependencies and web application.
  health            Verify API, worker, and web readiness.
  status            Show Compose service state.
  logs              Follow all Compose service logs.
  certify-headless  Run clean Journey 12 headlessly with retained evidence.
  record-headed     Run the paced headed Journey 12 recording.
  help              Show this command list.
EOF
}

prerequisites() {
  command -v docker >/dev/null
  command -v curl >/dev/null
  command -v node >/dev/null
  command -v python3 >/dev/null
  docker compose version >/dev/null
  python3 scripts/check_toolchain_versions.py
  printf 'POC prerequisites passed.\n'
}

start() {
  prerequisites
  "${compose[@]}" up --build -d --wait
  health
}

stop() {
  "${compose[@]}" down --remove-orphans
}

start_api() {
  "${compose[@]}" up --build -d --wait postgres minio api
}

migrate() {
  start_api
  "${compose[@]}" exec -T api python -m app.manage migrate
}

seed() {
  start_api
  "${compose[@]}" exec -T api python -m app.manage seed
}

reset() {
  "${compose[@]}" stop worker >/dev/null 2>&1 || true
  "${compose[@]}" up --build -d --wait postgres minio api web
  "${compose[@]}" exec -T api python -m app.manage reset
  fingerprint="$("${compose[@]}" exec -T api python -m app.manage fingerprint | tail -n 1)"
  "${compose[@]}" up --build -d --wait worker
  printf 'Synthetic reset fingerprint: %s\n' "$fingerprint"
}

start_worker() {
  "${compose[@]}" up --build -d --wait worker
}

start_web() {
  "${compose[@]}" up --build -d --wait web
}

health() {
  api_port="${API_PORT:-8000}"
  web_port="${WEB_PORT:-4173}"
  curl --fail --silent --show-error "http://localhost:${api_port}/health/ready" >/dev/null
  curl --fail --silent --show-error "http://localhost:${web_port}/" >/dev/null
  "${compose[@]}" exec -T worker python -m app.worker_health
  printf 'API, worker, and web health checks passed.\n'
}

run_journey() {
  mode="$1"
  output="${2:-}"
  if [[ -n "$output" ]]; then
    exec bash scripts/run_journey12.sh "$mode" "$output"
  fi
  exec bash scripts/run_journey12.sh "$mode"
}

command="${1:-help}"
artifact_directory="${2:-}"

case "$command" in
  prerequisites) prerequisites ;;
  start) start ;;
  stop) stop ;;
  migrate) migrate ;;
  seed) seed ;;
  reset) reset ;;
  api) start_api ;;
  worker) start_worker ;;
  web) start_web ;;
  health) health ;;
  status) "${compose[@]}" ps ;;
  logs) "${compose[@]}" logs --follow ;;
  certify-headless) run_journey headless "$artifact_directory" ;;
  record-headed) run_journey headed "$artifact_directory" ;;
  help|-h|--help) usage ;;
  *)
    usage >&2
    exit 2
    ;;
esac
