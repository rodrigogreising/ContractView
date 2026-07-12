#!/usr/bin/env bash
set -euo pipefail

output_dir="${1:-artifacts/ci}"
project="${CI_PROJECT_NAME:-contractview-ci-local}"
compose=(docker compose -p "$project" -f compose.yaml -f compose.ci.yaml)
mkdir -p "$output_dir"

cleanup() {
  "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

fingerprints=()
for pass in 1 2; do
  cleanup
  "${compose[@]}" up -d --build postgres minio api web
  "${compose[@]}" exec -T api python -m app.manage reset
  fingerprints+=("$("${compose[@]}" exec -T api python -m app.manage fingerprint | tail -n 1)")
  "${compose[@]}" exec -T api pytest -q | tee "$output_dir/api-pass-$pass.log"
  "${compose[@]}" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')"
  "${compose[@]}" exec -T web wget --quiet --tries=1 --spider http://127.0.0.1/
  "${compose[@]}" up -d --build worker
  "${compose[@]}" exec -T worker python -m app.worker_health
  "${compose[@]}" ps --format json > "$output_dir/compose-pass-$pass.jsonl"
done

if [[ "${fingerprints[0]}" != "${fingerprints[1]}" ]]; then
  echo "Clean reset fingerprints differ: ${fingerprints[*]}" >&2
  exit 1
fi
printf '%s\n' "${fingerprints[0]}" > "$output_dir/reset-fingerprint.sha256"
printf 'Hermetic Compose certification passed twice with fingerprint %s.\n' "${fingerprints[0]}"
