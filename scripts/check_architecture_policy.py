"""Validate ContractView's modular-monolith architecture contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_LAYERS = {"domain", "application", "persistence", "integration", "worker", "http"}
REQUIRED_PROCESSES = {"web", "api", "worker", "postgresql", "minio"}
REQUIRED_CAPABILITIES = {
    "identity",
    "configuration",
    "artifacts",
    "extraction",
    "invoices",
    "validation",
    "packages",
    "workflow",
    "provenance",
}
REQUIRED_PRIMITIVES = {
    "Artifact",
    "Schema",
    "Field",
    "Entity",
    "Relation",
    "Rule",
    "Workflow",
    "View",
    "Template",
    "Event",
    "ValidationRun",
    "ConfigurationBundle",
    "InvoiceSnapshot",
    "PackageManifest",
}
REQUIRED_VERSIONS = {
    "artifact_version",
    "invoice_snapshot",
    "contract_version",
    "budget_version",
    "configuration_bundle_version",
    "schema_version",
    "mapping_version",
    "rule_version",
    "workflow_version",
    "view_version",
    "template_version",
    "parser_model_version",
}
REQUIRED_CLOSED_VOCABULARIES = {
    "lifecycle_states",
    "actor_roles",
    "resource_kinds",
    "reason_codes",
    "event_names",
    "relation_kinds",
}
REQUIRED_COLLABORATION = {
    "application-command-port",
    "application-query-port",
    "versioned-domain-event",
    "declared-read-model",
}
REQUIRED_DOCS = {
    "docs/adr/0002-role-based-poc-runtime.md": "modular-monolith-policy.json",
    "docs/architecture/system-map.md": "modular-monolith",
    "docs/architecture/data-flow.md": "modular-monolith",
    "docs/architecture/domain-model.md": "modular-monolith",
    "docs/architecture/service-boundaries.md": "modular-monolith",
    "docs/architecture/poc-boundary-review.md": "modular-monolith",
    "docs/sdlc/requirements-traceability.md": "SUB-59",
    "packages/README.md": "modular-monolith",
    "services/README.md": "modular-monolith",
    "apps/README.md": "modular-monolith",
}


def _cycle(nodes: dict[str, object], dependency_key: str) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str, path: list[str]) -> list[str] | None:
        if name in visiting:
            start = path.index(name)
            return path[start:] + [name]
        if name in visited:
            return None
        visiting.add(name)
        value = nodes.get(name)
        dependencies = value.get(dependency_key, []) if isinstance(value, dict) else []
        for dependency in dependencies:
            found = visit(str(dependency), path + [name])
            if found:
                return found
        visiting.remove(name)
        visited.add(name)
        return None

    for node in nodes:
        found = visit(node, [])
        if found:
            return found
    return None


def validate_policy(policy: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if policy.get("deploymentModel") != "modular-monolith":
        failures.append("deploymentModel must be modular-monolith")
    processes = set(policy.get("processes", []))
    if processes != REQUIRED_PROCESSES:
        failures.append(
            f"processes mismatch; missing={sorted(REQUIRED_PROCESSES - processes)}, "
            f"extra={sorted(processes - REQUIRED_PROCESSES)}"
        )

    layers = policy.get("layers")
    if not isinstance(layers, dict):
        failures.append("layers must be an object")
    else:
        missing = sorted(REQUIRED_LAYERS - layers.keys())
        extra = sorted(layers.keys() - REQUIRED_LAYERS)
        if missing or extra:
            failures.append(f"layers mismatch; missing={missing}, extra={extra}")
        for name, value in layers.items():
            if not isinstance(value, dict):
                failures.append(f"layer {name} must be an object")
                continue
            rank = value.get("rank")
            dependencies = value.get("allowedDependencies")
            if not isinstance(rank, int) or not isinstance(dependencies, list):
                failures.append(f"layer {name} must declare rank and allowedDependencies")
                continue
            for dependency in dependencies:
                dependency_value = layers.get(str(dependency))
                if not isinstance(dependency_value, dict):
                    failures.append(f"layer {name} depends on unknown layer {dependency}")
                elif not isinstance(dependency_value.get("rank"), int) or dependency_value["rank"] >= rank:
                    failures.append(f"layer inversion: {name} -> {dependency}")
        found_cycle = _cycle(layers, "allowedDependencies")
        if found_cycle:
            failures.append("layer dependency cycle: " + " -> ".join(found_cycle))

    if policy.get("compositionRootLayer") != "integration":
        failures.append("composition root must be owned by integration")

    capabilities = policy.get("capabilities")
    if not isinstance(capabilities, dict):
        failures.append("capabilities must be an object")
    else:
        missing = sorted(REQUIRED_CAPABILITIES - capabilities.keys())
        if missing:
            failures.append("missing capabilities: " + ", ".join(missing))
        owners: dict[str, str] = {}
        for name, value in capabilities.items():
            if not isinstance(value, dict):
                failures.append(f"capability {name} must be an object")
                continue
            owned = value.get("ownsData")
            dependencies = value.get("allowedApplicationDependencies")
            if not isinstance(owned, list) or not owned:
                failures.append(f"capability {name} must own canonical data")
            else:
                for data_name in owned:
                    prior = owners.get(str(data_name))
                    if prior:
                        failures.append(
                            f"duplicate data ownership: {data_name} owned by {prior} and {name}"
                        )
                    owners[str(data_name)] = name
            if not isinstance(dependencies, list):
                failures.append(f"capability {name} must declare application dependencies")
            else:
                for dependency in dependencies:
                    if dependency == name:
                        failures.append(f"capability {name} depends on itself")
                    elif dependency not in capabilities:
                        failures.append(f"capability {name} depends on unknown {dependency}")
        found_cycle = _cycle(capabilities, "allowedApplicationDependencies")
        if found_cycle:
            failures.append("capability dependency cycle: " + " -> ".join(found_cycle))

    persistence = policy.get("persistenceRules")
    if not isinstance(persistence, dict):
        failures.append("persistenceRules must be an object")
    else:
        expected = {
            "repositoryPortsOwnedByLayer": "application",
            "unitOfWorkOwnedByLayer": "application",
            "sharedDatabaseMeansSharedOwnership": False,
            "crossCapabilitySql": "forbidden",
            "crossCapabilityWrites": "forbidden",
            "crossCapabilityCommandJoins": "forbidden",
            "sqlAllowedOnlyInLayer": "persistence",
        }
        for key, value in expected.items():
            if persistence.get(key) != value:
                failures.append(f"persistence rule {key} must be {value!r}")

    collaboration = set(policy.get("collaborationMechanisms", []))
    if collaboration != REQUIRED_COLLABORATION:
        failures.append("capability collaboration mechanisms are incomplete")

    ontology = policy.get("ontology")
    if not isinstance(ontology, dict):
        failures.append("ontology must be an object")
    else:
        primitives = set(ontology.get("primitives", []))
        configuration = set(ontology.get("configurationContracts", []))
        runtime = set(ontology.get("runtimeContracts", []))
        if missing := sorted(REQUIRED_PRIMITIVES - primitives):
            failures.append("missing ontology primitives: " + ", ".join(missing))
        if overlap := sorted(configuration & runtime):
            failures.append("configuration/runtime contract overlap: " + ", ".join(overlap))
        if not (configuration | runtime) <= primitives:
            failures.append("configuration/runtime contracts must be ontology primitives")
        vocabularies = set(ontology.get("closedVocabularies", []))
        if missing := sorted(REQUIRED_CLOSED_VOCABULARIES - vocabularies):
            failures.append("missing closed vocabularies: " + ", ".join(missing))
        versions = set(ontology.get("requiredVersionReferences", []))
        if missing := sorted(REQUIRED_VERSIONS - versions):
            failures.append("missing version references: " + ", ".join(missing))
        if ontology.get("unknownVocabularyBehavior") != "reject":
            failures.append("unknown ontology vocabulary must be rejected")

    config_runtime = policy.get("configurationRuntimeRules")
    expected_config_runtime = {
        "activationIsProspective": True,
        "activeConfigurationIsImmutable": True,
        "runtimeReferencesExactVersions": True,
        "historicalRuntimeMutation": "forbidden",
        "revalidationCreatesNewRecord": True,
        "regenerationCreatesNewRecord": True,
    }
    if not isinstance(config_runtime, dict):
        failures.append("configurationRuntimeRules must be an object")
    else:
        for key, value in expected_config_runtime.items():
            if config_runtime.get(key) != value:
                failures.append(f"configuration/runtime rule {key} must be {value!r}")

    extraction = policy.get("futureExtraction")
    if not isinstance(extraction, dict):
        failures.append("futureExtraction must be an object")
    else:
        for key in (
            "requiresApplicationPorts",
            "requiresVersionedEvents",
            "requiresIdempotency",
        ):
            if extraction.get(key) is not True:
                failures.append(f"future extraction rule {key} must be true")
        if extraction.get("permitsSharedTables") is not False:
            failures.append("future extracted services must not share tables")
        if extraction.get("addsNetworkServicesToPoc") is not False:
            failures.append("the POC must not add network service complexity")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("docs/architecture/modular-monolith-policy.json"),
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()

    repo = args.repo.resolve()
    policy_path = args.policy if args.policy.is_absolute() else repo / args.policy
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Architecture policy validation failed: {error}")
        return 1

    failures = validate_policy(policy)
    for relative, needle in REQUIRED_DOCS.items():
        path = repo / relative
        if not path.is_file():
            failures.append(f"missing architecture evidence: {relative}")
        elif needle not in path.read_text(encoding="utf-8"):
            failures.append(f"{relative} does not reference {needle!r}")

    if failures:
        print("Architecture policy validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Architecture policy validation passed (6 layers, 9 capability owners).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
