#!/usr/bin/env bash
set -euo pipefail

# Backward-compatible Journey 11 command. The MVP terminal scenario is Journey 12.
exec bash scripts/run_journey12.sh "$@"
