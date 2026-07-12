import copy
import unittest

from scripts.check_shared_contracts import (
    breaking_changes, compatibility_examples, requiredness_examples, validate,
)
from scripts.generate_shared_contracts import load


class SharedContractPolicyTests(unittest.TestCase):
    def test_registries_and_generated_consumers_are_current(self):
        self.assertEqual(validate(), [])

    def test_additive_optional_field_is_compatible(self):
        additive, _ = compatibility_examples()
        self.assertEqual(additive, [])

    def test_closed_vocabulary_change_is_breaking(self):
        _, breaking = compatibility_examples()
        self.assertEqual(breaking, ["closed vocabulary changed: actorRoles"])

    def test_field_type_change_is_breaking(self):
        source = load()["domain"]
        changed = copy.deepcopy(source)
        changed["contracts"]["Artifact"]["fields"][5]["type"] = "string"
        self.assertIn(
            "field contract changed: Artifact.byteSize",
            breaking_changes(source, changed),
        )

    def test_typescript_requiredness_is_derived_from_registry_fields(self):
        optional, required = requiredness_examples()
        self.assertEqual(optional, "  submitted?: boolean;")
        self.assertEqual(required, "  normalizedInput: Record<string, unknown>;")


if __name__ == "__main__":
    unittest.main()
