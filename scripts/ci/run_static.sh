#!/usr/bin/env bash
set -euo pipefail

python3 scripts/check_toolchain_versions.py
python3 scripts/check_formatting.py
python3 -m ruff check services/api-workflow/app scripts
python3 -m mypy services/api-workflow/app scripts
python3 scripts/check_shared_contracts.py
python3 scripts/check_persistence_statements.py
python3 scripts/check_module_boundaries.py
python3 scripts/check_architecture_policy.py
python3 scripts/check_sdlc_delivery_policy.py
python3 scripts/check_recovery_certification.py
python3 -m pytest -q scripts/tests
npm --prefix apps/web-app test
npm --prefix apps/web-app run build
python3 scripts/check_web_boundaries.py
