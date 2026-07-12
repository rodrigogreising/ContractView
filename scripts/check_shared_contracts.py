"""Validate shared-contract registries, generated consumers, and evolution rules."""

from __future__ import annotations

import re
from copy import deepcopy

try:
    from scripts.generate_shared_contracts import (
        PYTHON_PRIMITIVES, SOURCES, contract_definitions, load, outputs,
        typescript_field, vocabulary_definitions,
    )
except ModuleNotFoundError:  # Direct `python scripts/check_shared_contracts.py` execution.
    from generate_shared_contracts import (
        PYTHON_PRIMITIVES, SOURCES, contract_definitions, load, outputs,
        typescript_field, vocabulary_definitions,
    )

REQUIRED_CONTRACTS = {
    "VersionReference", "ActorReference", "Artifact", "TypedField", "Entity", "Relation",
    "RuleDefinition", "RuleResult", "ValidationRun", "Workflow", "View", "Template",
    "EventEnvelope", "ConfigurationBundle", "IdentityDto",
    "ActiveConfigurationDto", "ValidationRunDto",
    "ExtractionComponentVersion", "ValidationInputManifest", "PackageFileDigest",
    "PackageBuildInput", "PackageReproductionManifest",
}


def breaking_changes(old: dict, new: dict) -> list[str]:
    failures: list[str] = []
    for name, definition in old.get("vocabularies", {}).items():
        candidate = new.get("vocabularies", {}).get(name)
        if not candidate or set(candidate.get("values", [])) != set(definition["values"]):
            failures.append(f"closed vocabulary changed: {name}")
    for name, contract in old.get("contracts", {}).items():
        candidate = new.get("contracts", {}).get(name)
        if not candidate:
            failures.append(f"contract removed: {name}")
            continue
        old_fields = {field["name"]: field for field in contract["fields"]}
        new_fields = {field["name"]: field for field in candidate["fields"]}
        for field_name in old_fields.keys() - new_fields.keys():
            failures.append(f"field removed: {name}.{field_name}")
        for field_name in new_fields.keys() - old_fields.keys():
            if new_fields[field_name]["required"]:
                failures.append(f"required field added: {name}.{field_name}")
        for field_name in old_fields.keys() & new_fields.keys():
            old_shape = {key: value for key, value in old_fields[field_name].items() if key != "name"}
            new_shape = {key: value for key, value in new_fields[field_name].items() if key != "name"}
            if old_shape != new_shape:
                failures.append(f"field contract changed: {name}.{field_name}")
    return failures


def _base_types(type_name: str) -> set[str]:
    if type_name.endswith("[]"):
        return _base_types(type_name[:-2])
    if type_name.startswith("map<string,") and type_name.endswith(">"):
        return _base_types(type_name[11:-1])
    return set(type_name.split("|"))


def validate() -> list[str]:
    registry = load()
    failures: list[str] = []
    contracts = {name for item in registry.values() for name in item.get("contracts", {})}
    missing = REQUIRED_CONTRACTS - contracts
    if missing:
        failures.append("missing contracts: " + ", ".join(sorted(missing)))
    if registry["domain"]["vocabularies"]["configurationLifecycle"]["values"] != registry["configuration"]["vocabularies"]["lifecycle"]["values"]:
        failures.append("configuration lifecycle vocabulary drift")
    vocabulary_types = {
        definition["python"]
        for _, definition in vocabulary_definitions(registry)
        if definition.get("python")
    }
    model_types = {definition["model"] for _, definition in contract_definitions(registry)}
    known_types = set(PYTHON_PRIMITIVES) | vocabulary_types | model_types
    for name, item in registry.items():
        if not re.fullmatch(r"\d+\.\d+\.\d+", item["version"]):
            failures.append(f"{name} version is not semantic")
        for vocabulary, definition in item.get("vocabularies", {}).items():
            values = definition["values"]
            if len(values) != len(set(values)):
                failures.append(f"{name}.{vocabulary} contains duplicates")
        for contract_name, contract in item.get("contracts", {}).items():
            field_names = [field["name"] for field in contract.get("fields", [])]
            if not field_names:
                failures.append(f"{name}.{contract_name} has no typed fields")
            if len(field_names) != len(set(field_names)):
                failures.append(f"{name}.{contract_name} contains duplicate fields")
            for field in contract.get("fields", []):
                if not isinstance(field.get("required"), bool):
                    failures.append(f"{name}.{contract_name}.{field.get('name')} lacks requiredness")
                unknown = _base_types(field.get("type", "")) - known_types
                if unknown:
                    failures.append(
                        f"{name}.{contract_name}.{field.get('name')} has unknown types: "
                        + ", ".join(sorted(unknown))
                    )
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
    package_versions = {item["package"]: item["version"] for item in registry.values()}
    for item in registry.values():
        for dependency, requirement in item.get("dependsOn", {}).items():
            if not re.fullmatch(r"\^\d+\.\d+\.\d+", requirement):
                failures.append(f"invalid dependency range {item['package']}->{dependency}")
            elif dependency in package_versions and requirement[1:].split(".")[0] != package_versions[dependency].split(".")[0]:
                failures.append(f"incompatible dependency major {item['package']}->{dependency}")
    for path, expected in outputs().items():
        if not path.exists() or path.read_text() != expected:
            failures.append(f"generated consumer is stale: {path.name}")
    return failures


def compatibility_examples() -> tuple[list[str], list[str]]:
    source = load()["domain"]
    additive = deepcopy(source)
    additive["contracts"]["Artifact"]["fields"].append(
        {"name": "label", "type": "string", "required": False}
    )
    breaking = deepcopy(source)
    breaking["vocabularies"]["actorRoles"]["values"].append("superuser")
    return breaking_changes(source, additive), breaking_changes(source, breaking)


def requiredness_examples() -> tuple[str, str]:
    """Expose renderer output used by parity regression tests."""
    optional = {"name": "submitted", "type": "boolean", "required": False, "default": False}
    required = {"name": "normalizedInput", "type": "map<string,any>", "required": True}
    return typescript_field(optional), typescript_field(required)


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
