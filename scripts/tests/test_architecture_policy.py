from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/check_architecture_policy.py"
POLICY_PATH = ROOT / "docs/architecture/modular-monolith-policy.json"
SPEC = importlib.util.spec_from_file_location("check_architecture_policy", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


class ArchitecturePolicyTests(unittest.TestCase):
    def test_repository_policy_is_valid(self) -> None:
        self.assertEqual([], MODULE.validate_policy(policy()))

    def test_layer_inversion_fails(self) -> None:
        value = policy()
        value["layers"]["domain"]["allowedDependencies"] = ["http"]  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("layer inversion" in failure for failure in failures))

    def test_duplicate_data_ownership_fails(self) -> None:
        value = policy()
        value["capabilities"]["workflow"]["ownsData"].append("invoice_snapshots")  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("duplicate data ownership" in failure for failure in failures))

    def test_cross_capability_sql_must_be_forbidden(self) -> None:
        value = policy()
        value["persistenceRules"]["crossCapabilitySql"] = "allowed"  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("crossCapabilitySql" in failure for failure in failures))

    def test_missing_required_capability_fails(self) -> None:
        value = policy()
        del value["capabilities"]["provenance"]  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("missing capabilities" in failure for failure in failures))

    def test_capability_cycle_fails(self) -> None:
        value = policy()
        value["capabilities"]["provenance"]["allowedApplicationDependencies"] = [  # type: ignore[index]
            "workflow"
        ]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("capability dependency cycle" in failure for failure in failures))

    def test_configuration_runtime_overlap_fails(self) -> None:
        value = policy()
        value["ontology"]["runtimeContracts"].append("Schema")  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("configuration/runtime contract overlap" in failure for failure in failures))

    def test_unknown_ontology_vocabulary_must_reject(self) -> None:
        value = policy()
        value["ontology"]["unknownVocabularyBehavior"] = "accept"  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("unknown ontology vocabulary" in failure for failure in failures))

    def test_closed_vocabulary_is_required(self) -> None:
        value = policy()
        value["ontology"]["closedVocabularies"].remove("reason_codes")  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("missing closed vocabularies" in failure for failure in failures))

    def test_exact_version_references_are_required(self) -> None:
        value = policy()
        value["ontology"]["requiredVersionReferences"].remove("budget_version")  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("missing version references" in failure for failure in failures))

    def test_configuration_activation_must_be_prospective(self) -> None:
        value = policy()
        value["configurationRuntimeRules"]["activationIsProspective"] = False  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("activationIsProspective" in failure for failure in failures))

    def test_poc_process_set_cannot_add_network_services(self) -> None:
        value = policy()
        value["processes"].append("validation-service")  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("processes mismatch" in failure for failure in failures))

    def test_future_services_cannot_share_tables(self) -> None:
        value = copy.deepcopy(policy())
        value["futureExtraction"]["permitsSharedTables"] = True  # type: ignore[index]
        failures = MODULE.validate_policy(value)
        self.assertTrue(any("must not share tables" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
