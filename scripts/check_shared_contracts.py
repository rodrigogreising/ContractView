"""Validate shared-contract registries, generated consumers, and evolution rules."""

from __future__ import annotations

import re
from copy import deepcopy

try:
    from scripts.generate_shared_contracts import SOURCES, load, outputs
except ModuleNotFoundError:  # Direct `python scripts/check_shared_contracts.py` execution.
    from generate_shared_contracts import SOURCES, load, outputs

REQUIRED_CONTRACTS = {
    "VersionReference", "ActorReference", "Artifact", "TypedField", "Entity", "Relation",
    "RuleDefinition", "RuleResult", "ValidationRun", "Workflow", "View", "Template",
    "EventEnvelope", "ConfigurationBundle",
}


def breaking_changes(old: dict, new: dict) -> list[str]:
    failures: list[str] = []
    for name, values in old.get("vocabularies", {}).items():
        if set(new.get("vocabularies", {}).get(name, [])) != set(values):
            failures.append(f"closed vocabulary changed: {name}")
    for name, contract in old.get("contracts", {}).items():
        candidate = new.get("contracts", {}).get(name)
        if not candidate:
            failures.append(f"contract removed: {name}")
            continue
        old_required = set(contract.get("required", []))
        new_required = set(candidate.get("required", []))
        if new_required - old_required:
            failures.append(f"required fields added: {name}")
        if old_required - new_required:
            failures.append(f"required fields removed: {name}")
        if set(contract.get("optional", [])) - set(candidate.get("optional", [])):
            failures.append(f"optional fields removed: {name}")
    return failures


def validate() -> list[str]:
    registry = load()
    failures: list[str] = []
    contracts = {name for item in registry.values() for name in item.get("contracts", {})}
    missing = REQUIRED_CONTRACTS - contracts
    if missing:
        failures.append("missing contracts: " + ", ".join(sorted(missing)))
    if registry["domain"]["vocabularies"]["configurationLifecycle"] != registry["configuration"]["vocabularies"]["lifecycle"]:
        failures.append("configuration lifecycle vocabulary drift")
    for name, item in registry.items():
        if not re.fullmatch(r"\d+\.\d+\.\d+", item["version"]):
            failures.append(f"{name} version is not semantic")
        for vocabulary, values in item.get("vocabularies", {}).items():
            if len(values) != len(set(values)):
                failures.append(f"{name}.{vocabulary} contains duplicates")
    graph = {item["package"]: set(item.get("dependsOn", {})) for item in registry.values()}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visiting:
            failures.append(f"contract dependency cycle at {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, set()):
            if dependency not in graph:
                failures.append(f"unknown contract dependency {node}->{dependency}")
            else:
                visit(dependency)
        visiting.remove(node)
        visited.add(node)
    for node in graph:
        visit(node)
    for path, expected in outputs().items():
        if not path.exists() or path.read_text() != expected:
            failures.append(f"generated consumer is stale: {path.name}")
    return failures


def compatibility_examples() -> tuple[list[str], list[str]]:
    source = load()["domain"]
    additive = deepcopy(source)
    additive["contracts"]["Artifact"]["optional"].append("label")
    breaking = deepcopy(source)
    breaking["vocabularies"]["actorRoles"].append("superuser")
    return breaking_changes(source, additive), breaking_changes(source, breaking)


def main() -> int:
    failures = validate()
    if failures:
        print("Shared contract validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    registry = load()
    print(f"Shared contract validation passed ({len(SOURCES)} registries, {sum(len(x['contracts']) for x in registry.values())} contracts).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
