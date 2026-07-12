import unittest

from scripts.check_shared_contracts import compatibility_examples, validate


class SharedContractPolicyTests(unittest.TestCase):
    def test_registries_and_generated_consumers_are_current(self):
        self.assertEqual(validate(), [])

    def test_additive_optional_field_is_compatible(self):
        additive, _ = compatibility_examples()
        self.assertEqual(additive, [])

    def test_closed_vocabulary_change_is_breaking(self):
        _, breaking = compatibility_examples()
        self.assertEqual(breaking, ["closed vocabulary changed: actorRoles"])


if __name__ == "__main__":
    unittest.main()
