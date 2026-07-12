from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "publication" / "build_candidate.py"
SPEC = importlib.util.spec_from_file_location("build_publication_candidate", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

CERTIFIER_PATH = (
    Path(__file__).resolve().parents[1] / "publication" / "certify_candidate.py"
)
CERTIFIER_SPEC = importlib.util.spec_from_file_location(
    "certify_publication_candidate", CERTIFIER_PATH
)
assert CERTIFIER_SPEC and CERTIFIER_SPEC.loader
CERTIFIER = importlib.util.module_from_spec(CERTIFIER_SPEC)
sys.modules[CERTIFIER_SPEC.name] = CERTIFIER
CERTIFIER_SPEC.loader.exec_module(CERTIFIER)


class PublicationCandidateTests(unittest.TestCase):
    def test_internal_evidence_is_excluded(self) -> None:
        self.assertFalse(MODULE.included("docs/sdlc/implementation/SUB-57.md"))
        self.assertFalse(MODULE.included("solution_requirements.md"))
        self.assertFalse(MODULE.included("scripts/publication/build_candidate.py"))
        self.assertFalse(MODULE.included(".agents/skills/private/SKILL.md"))
        self.assertFalse(MODULE.included("docs/codex/sdlc-linear-control-plane.md"))
        self.assertFalse(MODULE.included("docs/architecture/poc-boundary-review.md"))
        self.assertTrue(MODULE.included("services/api-workflow/app/main.py"))
        self.assertTrue(MODULE.included("docs/architecture/domain-model.md"))

    def test_neutral_identity_rewrite_is_complete(self) -> None:
        transformed = MODULE.neutralize(
            "ContractView contractview CONTRACTVIEW @contractview/web-app SUB-79 REC-12"
        )
        self.assertNotIn("contractview", transformed.lower())
        self.assertIn(MODULE.PUBLIC_TITLE, transformed)
        self.assertIn(MODULE.PUBLIC_IDENTIFIER, transformed)
        self.assertNotIn("SUB-79", transformed)
        self.assertNotIn("REC-12", transformed)

    def test_rejects_non_reserved_identity_and_secret_shapes(self) -> None:
        failures: list[str] = []
        MODULE.verify_text(
            Path("example.txt"),
            "contact person@company.example and token ghp_12345678901234567890",
            failures,
        )
        self.assertEqual(2, len(failures))

    def test_build_has_no_history_and_a_hash_for_every_exported_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / MODULE.PUBLIC_SLUG
            manifest = MODULE.build(output, "a" * 40)
            self.assertFalse((output / ".git").exists())
            self.assertFalse(manifest["gitHistoryIncluded"])
            self.assertFalse(manifest["privateControlPlaneIncluded"])
            self.assertEqual(
                set(manifest["fileHashes"]),
                {
                    str(path.relative_to(output))
                    for path in output.rglob("*")
                    if path.is_file() and path.name != "PUBLICATION-MANIFEST.json"
                },
            )
            persisted = json.loads(
                (output / "PUBLICATION-MANIFEST.json").read_text(encoding="utf-8")
            )
            self.assertEqual(MODULE.PUBLIC_SLUG, persisted["repositorySlug"])
            self.assertNotIn("excludedSourcePaths", persisted)
            self.assertGreater(persisted["excludedSourceFileCount"], 0)

    def test_certifier_rejects_a_changed_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory)
            source = candidate / "source.txt"
            source.write_text("original", encoding="utf-8")
            manifest = {"fileHashes": {"source.txt": CERTIFIER.digest(source)}}
            CERTIFIER.verify_source_hashes(candidate, manifest)
            source.write_text("changed", encoding="utf-8")
            with self.assertRaises(SystemExit):
                CERTIFIER.verify_source_hashes(candidate, manifest)

    def test_certifier_rejects_an_unhashed_extra_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory)
            source = candidate / "source.txt"
            source.write_text("original", encoding="utf-8")
            manifest = {"fileHashes": {"source.txt": CERTIFIER.digest(source)}}
            (candidate / "unexpected.txt").write_text("extra", encoding="utf-8")
            with self.assertRaises(SystemExit):
                CERTIFIER.verify_source_hashes(candidate, manifest)

    def test_private_control_plane_reference_is_rejected(self) -> None:
        failures: list[str] = []
        MODULE.verify_text(Path("README.md"), "internal SUB-79 evidence", failures)
        self.assertEqual(["README.md: contains a private control-plane reference"], failures)

    def test_certifier_counts_colored_test_summaries(self) -> None:
        self.assertEqual(177, CERTIFIER.count_pytest("\x1b[32m177 passed in 9.2s\x1b[0m\n"))
        self.assertEqual(13, CERTIFIER.count_vitest(" Tests  13 passed (13)\n"))
        self.assertEqual(18, CERTIFIER.count_unittest("Ran 18 tests in 0.127s\n"))


if __name__ == "__main__":
    unittest.main()
