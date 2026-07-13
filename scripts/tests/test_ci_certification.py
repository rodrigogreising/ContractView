from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOLCHAINS = load("check_toolchain_versions", SCRIPTS / "check_toolchain_versions.py")
MANIFEST = load("write_ci_manifest", SCRIPTS / "ci" / "write_ci_manifest.py")
BRANCH_PROTECTION = load(
    "capture_branch_protection", SCRIPTS / "ci" / "capture_branch_protection.py"
)


class CiCertificationTests(unittest.TestCase):
    def test_pr_workflow_checks_out_and_fetches_immutable_review_history(self) -> None:
        workflow = (ROOT / ".github/workflows/contractview-ci.yml").read_text()
        self.assertIn("github.event.pull_request.head.sha", workflow)
        self.assertIn("git rev-parse --is-shallow-repository", workflow)
        self.assertIn("refs/remotes/origin/${{ github.event.pull_request.base.ref }}", workflow)
        self.assertIn("git merge-base --is-ancestor", workflow)
        self.assertIn("Paced headed Journey 12 browser certification", workflow)
        self.assertIn("xvfb-run --auto-servernum", workflow)
        self.assertIn("include-hidden-files: true", workflow)

    def test_numeric_version_ignores_tool_prefix(self) -> None:
        self.assertEqual((20, 20, 2), TOOLCHAINS.numeric_version("v20.20.2"))
        self.assertEqual((3, 12, 13), TOOLCHAINS.numeric_version("Python 3.12.13"))

    def test_test_count_covers_pytest_and_vitest(self) -> None:
        content = (
            "46 passed in 0.19s\n"
            "\x1b[2m Test Files \x1b[22m \x1b[1m\x1b[32m2 passed\x1b[39m\x1b[22m (2)\n"
            "\x1b[2m      Tests \x1b[22m \x1b[1m\x1b[32m13 passed\x1b[39m\x1b[22m (13)\n"
            "176 passed in 4.0s\n"
        )
        self.assertEqual(235, MANIFEST.count_tests(content))

    def test_manifest_rejects_evidence_without_passing_tests(self) -> None:
        with self.assertRaisesRegex(SystemExit, "no passing test count"):
            MANIFEST.required_test_count("Static", "1 failed in 0.2s\n")

    def test_playwright_result_requires_one_clean_expected_test(self) -> None:
        self.assertEqual(
            1,
            MANIFEST.playwright_test_count(
                {"stats": {"expected": 1, "unexpected": 0, "flaky": 0}}
            ),
        )
        with self.assertRaisesRegex(SystemExit, "not clean"):
            MANIFEST.playwright_test_count(
                {"stats": {"expected": 1, "unexpected": 1, "flaky": 0}}
            )

    def test_retained_artifacts_are_hashed_and_manifest_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "static.log").write_text("passed\n", encoding="utf-8")
            (root / "manifest.json").write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                {"static.log": sha256(b"passed\n").hexdigest()},
                MANIFEST.file_hashes(root),
            )

    def test_prerequisites_are_machine_validated(self) -> None:
        merge_sha = "a" * 40
        self.assertEqual(
            [
                {
                    "issue": "SUB-57",
                    "mergeSha": merge_sha,
                    "postMergeVerified": True,
                }
            ],
            MANIFEST.validate_prerequisites(
                "SUB-67",
                {
                    "SUB-67": [
                        {
                            "issue": "SUB-57",
                            "mergeSha": merge_sha,
                            "postMergeVerified": True,
                        }
                    ]
                },
                lambda candidate: candidate == merge_sha,
            ),
        )

    def test_issue_evidence_coverage_is_complete(self) -> None:
        for issue in ("SUB-26", "SUB-53", "SUB-55"):
            with self.subTest(issue=issue):
                profile = MANIFEST.load_evidence_coverage(issue)
                self.assertEqual(
                    set(profile["riskAndGateLabels"]),
                    set(profile["riskCoverage"]),
                )
                self.assertTrue(profile["reviewSkills"])
        sub_26 = MANIFEST.load_evidence_coverage("SUB-26")
        self.assertIn("risk:human-authority", sub_26["riskAndGateLabels"])
        sub_53 = MANIFEST.load_evidence_coverage("SUB-53")
        self.assertIn("cv-review-operations-postmortem", sub_53["reviewSkills"])
        sub_55 = MANIFEST.load_evidence_coverage("SUB-55")
        self.assertEqual("Evidence Review", sub_55["projectStatus"])
        self.assertTrue(sub_55["includeJourneyInCleanRuntime"])
        self.assertIn("risk:ai-authority", sub_55["riskAndGateLabels"])

    def test_stale_prerequisite_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "not an ancestor of the PR base"):
            MANIFEST.validate_prerequisites(
                "SUB-67",
                {
                    "SUB-67": [
                        {
                            "issue": "SUB-57",
                            "mergeSha": "a" * 40,
                            "postMergeVerified": True,
                        }
                    ]
                },
                lambda _candidate: False,
            )

    def test_branch_protection_is_sanitized_and_validated(self) -> None:
        record = BRANCH_PROTECTION.sanitize_and_validate(
            {
                "url": "https://api.github.test/private-detail",
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["certification"],
                },
                "enforce_admins": {"enabled": True},
                "allow_force_pushes": {"enabled": False},
                "allow_deletions": {"enabled": False},
            },
            "owner/repository",
            "master",
            "certification",
        )
        self.assertNotIn("url", record)
        self.assertEqual(["certification"], record["requiredStatusChecks"]["contexts"])

    def test_missing_required_check_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "does not require"):
            BRANCH_PROTECTION.sanitize_and_validate(
                {
                    "required_status_checks": {"strict": True, "contexts": []},
                    "enforce_admins": {"enabled": True},
                    "allow_force_pushes": {"enabled": False},
                    "allow_deletions": {"enabled": False},
                },
                "owner/repository",
                "master",
                "certification",
            )


if __name__ == "__main__":
    unittest.main()
