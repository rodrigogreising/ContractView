#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-headless}"
OUTPUT="${2:-artifacts/journey11/${MODE}-$(date -u +%Y%m%dT%H%M%SZ)}"
PROJECT="${JOURNEY11_PROJECT_NAME:-${CI_PROJECT_NAME:-contractview}-journey11}"
PORT="${JOURNEY11_WEB_PORT:-14173}"
COMPOSE=(docker compose -p "$PROJECT" -f compose.yaml -f compose.e2e.yaml)

if [[ "$MODE" != "headless" && "$MODE" != "headed" ]]; then
  echo "Usage: $0 [headless|headed] [artifact-directory]" >&2
  exit 2
fi

mkdir -p "$OUTPUT"

finish() {
  status=$?
  "${COMPOSE[@]}" ps --format json > "$OUTPUT/compose-services.jsonl" 2>/dev/null || true
  "${COMPOSE[@]}" logs --no-color > "$OUTPUT/runtime.log" 2>&1 || true
  if [[ "${JOURNEY11_KEEP_RUNTIME:-false}" != "true" ]]; then
    "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  exit "$status"
}
trap finish EXIT INT TERM

"${COMPOSE[@]}" down --volumes --remove-orphans
"${COMPOSE[@]}" up --build -d --wait postgres minio api web
"${COMPOSE[@]}" exec -T api python -m app.manage reset
"${COMPOSE[@]}" up -d --wait worker

npm ci --prefix tests/e2e
npm exec --prefix tests/e2e -- playwright install chromium

if [[ "$MODE" == "headed" ]]; then
  JOURNEY11_BASE_URL="http://127.0.0.1:${PORT}" \
  JOURNEY11_ARTIFACT_DIR="$(pwd)/$OUTPUT" \
  JOURNEY11_HEADED=true \
  JOURNEY11_SLOW_MO_MS="${JOURNEY11_SLOW_MO_MS:-650}" \
  npm run --prefix tests/e2e test:headed
else
  JOURNEY11_BASE_URL="http://127.0.0.1:${PORT}" \
  JOURNEY11_ARTIFACT_DIR="$(pwd)/$OUTPUT" \
  npm test --prefix tests/e2e
fi
