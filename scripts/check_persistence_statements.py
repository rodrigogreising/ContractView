"""Validate named SQL, capability repositories, and generated statement IDs."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "services/api-workflow/app"
POLICY_PATH = ROOT / "docs/architecture/module-ownership-policy.json"
CATALOG_PATH = APP / "adapters/persistence/statements.json"
ENUM_PATH = APP / "application/ports/statements.py"
SQL = re.compile(
    r"^\s*(?:select\b[\s\S]*\bfrom\b|insert\s+into\b|update\s+[a-z_]\w*\s+set\b|"
    r"delete\s+from\b|with\b[\s\S]*(?:select|update|insert|delete)\b)",
    re.I,
)
TABLE = r"[a-z_][a-z0-9_]*"
READ_TABLE = re.compile(rf"\b(?:from|join)\s+({TABLE})\b(?!\s*\()", re.I)
INSERT_TABLE = re.compile(rf"\binsert\s+into\s+({TABLE})\b", re.I)
UPDATE_TABLE = re.compile(rf"\bupdate\s+({TABLE})(?:\s+{TABLE})?\s+set\b", re.I)
DELETE_TABLE = re.compile(rf"\bdelete\s+from\s+({TABLE})\b", re.I)
CTE_NAME = re.compile(rf"(?:\bwith|,)\s*({TABLE})\s+as\s*\(", re.I)


def load() -> tuple[dict, dict]:
    return json.loads(POLICY_PATH.read_text()), json.loads(CATALOG_PATH.read_text())


def render_enum(catalog: dict[str, dict]) -> str:
    rows = "\n".join(f'    {name} = "{name}"' for name in sorted(catalog))
    return (
        '"""Generated application-owned statement identifiers; contains no SQL."""\n\n'
        "from enum import StrEnum\n\n\n"
        f"class Statement(StrEnum):\n{rows}\n"
    )


def _module_for_statement(name: str, policy: dict) -> str:
    return next(
        (
            candidate[:-3]
            for candidate in sorted(policy["moduleCapabilities"], key=len, reverse=True)
            if name.startswith(candidate[:-3].upper() + "_")
        ),
        "unknown",
    )


def code_paths() -> list[Path]:
    return sorted(
        path
        for path in APP.rglob("*.py")
        if "adapters/persistence" not in path.as_posix()
        and path.name not in {"manage.py", "runtime.py"}
    )


def sql_footprint(sql: str) -> tuple[set[str], set[str]]:
    """Derive physical read/write tables independently from catalog metadata."""

    cte_names = {match.group(1).lower() for match in CTE_NAME.finditer(sql)}
    writes = {
        match.group(1).lower()
        for pattern in (INSERT_TABLE, UPDATE_TABLE, DELETE_TABLE)
        for match in pattern.finditer(sql)
    }
    reads = {
        match.group(1).lower()
        for match in READ_TABLE.finditer(sql)
        if match.group(1).lower() not in cte_names
    }
    return reads, writes


def validate_catalog(policy: dict, catalog: dict) -> list[str]:
    failures: list[str] = []
    for name, definition in catalog.items():
        required = {
            "owner",
            "consumerCapability",
            "kind",
            "operation",
            "readTables",
            "writeTables",
            "sourceOwners",
            "sql",
        }
        missing = sorted(required - definition.keys())
        if missing:
            failures.append(f"statement metadata is incomplete: {name}: {', '.join(missing)}")
            continue
        sql = str(definition.get("sql", ""))
        actual_reads, actual_writes = sql_footprint(sql)
        declared_reads = set(definition.get("readTables", []))
        declared_writes = set(definition.get("writeTables", []))
        if actual_reads != declared_reads:
            failures.append(
                f"statement read-table metadata differs from SQL: {name} "
                f"(declared={sorted(declared_reads)}, actual={sorted(actual_reads)})"
            )
        if actual_writes != declared_writes:
            failures.append(
                f"statement write-table metadata differs from SQL: {name} "
                f"(declared={sorted(declared_writes)}, actual={sorted(actual_writes)})"
            )
        physical_tables = actual_reads | actual_writes
        unknown_tables = sorted(physical_tables - policy["tableOwners"].keys())
        if unknown_tables:
            failures.append(f"statement references unowned tables: {name}: {', '.join(unknown_tables)}")
        actual_source_owners = {
            policy["tableOwners"][table]
            for table in physical_tables
            if table in policy["tableOwners"]
        }
        if actual_source_owners != set(definition.get("sourceOwners", [])):
            failures.append(
                f"statement source-owner metadata differs from SQL: {name} "
                f"(declared={sorted(definition.get('sourceOwners', []))}, "
                f"actual={sorted(actual_source_owners)})"
            )
        actual_operation = "write" if actual_writes else "read"
        if definition.get("operation") != actual_operation:
            failures.append(
                f"statement operation metadata differs from SQL: {name} "
                f"(declared={definition.get('operation')}, actual={actual_operation})"
            )
        write_owners = {policy["tableOwners"].get(table) for table in definition["writeTables"]}
        if len(write_owners) > 1:
            failures.append(f"cross-capability write statement: {name}")
        if definition["writeTables"] and definition["owner"] not in write_owners:
            failures.append(f"statement owner cannot write table: {name}")
        if definition["operation"] == "write":
            foreign_reads = set(definition["sourceOwners"]) - {definition["owner"]}
            if foreign_reads:
                failures.append(f"cross-capability SQL in write statement: {name}")
        if definition["kind"] == "declared-read-model":
            module = _module_for_statement(name, policy)
            if module not in policy["declaredReadModels"]:
                failures.append(f"undeclared cross-capability read model: {name}")
    return failures


def validate() -> list[str]:
    failures: list[str] = []
    policy, catalog = load()
    if not ENUM_PATH.exists() or ENUM_PATH.read_text() != render_enum(catalog):
        failures.append("generated application statement identifiers are stale")

    used: set[str] = set()
    for path in code_paths():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and SQL.match(node.value):
                failures.append(f"inline SQL outside persistence adapter: {path.relative_to(APP)}:{node.lineno}")
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "Statement":
                used.add(node.attr)
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
                and node.args
                and isinstance(node.args[0], ast.Attribute)
                and isinstance(node.args[0].value, ast.Name)
                and node.args[0].value.id == "Statement"
            ):
                continue
            name = node.args[0].attr
            definition = catalog.get(name)
            if definition is None:
                continue
            expected = "read_models" if definition["kind"] == "declared-read-model" else definition["owner"]
            receiver = node.func.value
            actual = receiver.attr if isinstance(receiver, ast.Attribute) else "unit_of_work"
            if actual != expected:
                failures.append(
                    f"statement bypasses capability repository: {path.relative_to(APP)}:{node.lineno} "
                    f"uses {actual}, expected {expected}"
                )

    if missing := sorted(used - catalog.keys()):
        failures.append("used statements missing from catalog: " + ", ".join(missing))
    if stale := sorted(catalog.keys() - used):
        failures.append("unused persistence statements: " + ", ".join(stale))

    failures.extend(validate_catalog(policy, catalog))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    policy, catalog = load()
    if args.generate:
        ENUM_PATH.write_text(render_enum(catalog))
        print(f"Generated {len(catalog)} application statement identifiers.")
        return 0
    failures = validate()
    if failures:
        print("Persistence boundary validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Persistence boundary validation passed ({len(catalog)} named statements).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
