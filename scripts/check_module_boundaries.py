"""Enforce ContractView module layers, capability ownership, and SQL boundaries."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

try:
    from scripts.check_persistence_statements import (
        CATALOG_PATH,
        capability_for_path,
        sql_footprint,
        statement_use_failures,
        validate_catalog as validate_statement_catalog,
        validate as check_statements,
    )
except ModuleNotFoundError:
    from check_persistence_statements import (
        CATALOG_PATH,
        capability_for_path,
        sql_footprint,
        statement_use_failures,
        validate_catalog as validate_statement_catalog,
        validate as check_statements,
    )

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "services/api-workflow/app"
OWNERSHIP_PATH = ROOT / "docs/architecture/module-ownership-policy.json"
ARCHITECTURE_PATH = ROOT / "docs/architecture/modular-monolith-policy.json"
SQL = re.compile(
    r"^\s*(?:select\b[\s\S]*\bfrom\b|insert\s+into\b|update\s+[a-z_]\w*\s+set\b|"
    r"delete\s+from\b|with\b[\s\S]*(?:select|update|insert|delete)\b|"
    r"create\s+(?:table|schema)\b|alter\s+table\b|drop\s+(?:table|schema)\b)",
    re.I,
)
INFRASTRUCTURE_IMPORTS = {
    "argon2",
    "fastapi",
    "minio",
    "openpyxl",
    "psycopg",
    "pydantic_settings",
    "reportlab",
    "subprocess",
}


def load_policies() -> tuple[dict, dict]:
    return json.loads(OWNERSHIP_PATH.read_text()), json.loads(ARCHITECTURE_PATH.read_text())


def classify(relative: str, ownership: dict) -> str | None:
    matches = []
    for layer, patterns in ownership["layers"].items():
        for pattern in patterns:
            if relative == pattern or (pattern.endswith("/") and relative.startswith(pattern)):
                matches.append(layer)
                break
    return matches[0] if len(matches) == 1 else None


def layer_dependency_allowed(source: str, target: str, source_path: str) -> bool:
    if source == target:
        return True
    allowed = {
        "domain": {"domain"},
        "application": {"application", "domain"},
        "persistence": {"persistence", "application", "domain"},
        "integration": {"integration", "persistence", "application", "domain"},
        "worker": {"worker", "application", "domain"},
        "http": {"http", "application", "domain"},
    }
    if source_path in {"app/main.py", "app/worker.py", "app/worker_health.py"}:
        return target in {"integration", "http", "worker"}
    return target in allowed[source]


def _resolved_module(path: Path, node: ast.ImportFrom) -> str | None:
    relative = path.relative_to(APP_ROOT.parent).with_suffix("")
    current = list(relative.parts)
    package = current[:-1]
    if node.level:
        up = node.level - 1
        if up > len(package):
            return None
        base = package[: len(package) - up]
        if node.module:
            base.extend(node.module.split("."))
        return ".".join(base)
    return node.module


def _module_path(module: str | None) -> Path | None:
    if not module or not module.startswith("app"):
        return None
    base = APP_ROOT.parent.joinpath(*module.split("."))
    file_path = base.with_suffix(".py")
    if file_path.exists():
        return file_path
    init_path = base / "__init__.py"
    return init_path if init_path.exists() else None


def _imported_module_paths(path: Path, node: ast.Import | ast.ImportFrom) -> set[Path]:
    modules: set[str] = set()
    if isinstance(node, ast.Import):
        modules.update(alias.name for alias in node.names)
    else:
        base = _resolved_module(path, node)
        if base:
            modules.add(base)
            modules.update(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
    return {
        target
        for module in modules
        if (target := _module_path(module)) is not None
    }


def validate_catalog(catalog: dict, ownership: dict) -> list[str]:
    return validate_statement_catalog(ownership, catalog)


def validate() -> list[str]:
    ownership, architecture = load_policies()
    failures = check_statements()
    python_files = sorted(APP_ROOT.rglob("*.py"))
    classified: dict[Path, str] = {}
    for path in python_files:
        relative = path.relative_to(APP_ROOT.parent).as_posix()
        layer = classify(relative, ownership)
        if layer is None:
            failures.append(f"module has missing or ambiguous layer ownership: {relative}")
        else:
            classified[path] = layer

    for path, source_layer in classified.items():
        relative = path.relative_to(APP_ROOT.parent).as_posix()
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and SQL.match(node.value):
                if not any(relative == prefix or (prefix.endswith("/") and relative.startswith(prefix)) for prefix in ownership["sqlAllowedPaths"]):
                    failures.append(f"inline SQL outside persistence/integration: {relative}:{node.lineno}")
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".")[0] for alias in node.names}
                if source_layer in {"domain", "application"} and roots & INFRASTRUCTURE_IMPORTS:
                    failures.append(f"{source_layer} imports infrastructure in {relative}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    root = node.module.split(".")[0]
                    if source_layer in {"domain", "application"} and root in INFRASTRUCTURE_IMPORTS:
                        failures.append(f"{source_layer} imports infrastructure in {relative}:{node.lineno}")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                target_paths = _imported_module_paths(path, node)
                for target_path in target_paths:
                    if target_path not in classified:
                        continue
                    target_layer = classified[target_path]
                    if not layer_dependency_allowed(source_layer, target_layer, relative):
                        failures.append(
                            f"forbidden layer import {source_layer}->{target_layer}: "
                            f"{relative}:{node.lineno}"
                        )

        source_capability = capability_for_path(path, ownership)
        if source_capability and source_capability != "shared":
            allowed_capabilities = set(
                architecture["capabilities"].get(source_capability, {}).get(
                    "allowedApplicationDependencies",
                    ownership.get("entrypointCapabilityDependencies", {}).get(
                        source_capability, []
                    ),
                )
            ) | {source_capability, "shared"}
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                for target_path in _imported_module_paths(path, node):
                    target_capability = ownership["moduleCapabilities"].get(target_path.name)
                    if target_capability and target_capability not in allowed_capabilities:
                        failures.append(
                            f"undeclared capability dependency {source_capability}->{target_capability}: "
                            f"{relative}:{node.lineno}"
                        )

    known_tables = set(ownership["tableOwners"])
    for migration in sorted((ROOT / "services/api-workflow/migrations").glob("*.sql")):
        mentioned = set(
            re.findall(
                r"\b(?:table(?:\s+if\s+not\s+exists)?|references)\s+([a-z_][a-z0-9_]*)",
                migration.read_text(),
                re.I,
            )
        )
        unknown = sorted(table.lower() for table in mentioned if table.lower() not in known_tables)
        if unknown:
            failures.append(f"migration tables lack capability owner {migration.name}: {', '.join(unknown)}")

    catalog = json.loads((APP_ROOT / "adapters/persistence/statements.json").read_text())
    failures.extend(validate_catalog(catalog, ownership))
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("Module boundary validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    ownership, _ = load_policies()
    print(
        f"Module boundary validation passed ({len(ownership['tableOwners'])} table owners, "
        f"{len(json.loads((APP_ROOT / 'adapters/persistence/statements.json').read_text()))} statements)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
