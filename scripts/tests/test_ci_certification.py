from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOLCHAINS = load("check_toolchain_versions", SCRIPTS / "check_toolchain_versions.py")
MANIFEST = load("write_ci_manifest", SCRIPTS / "ci" / "write_ci_manifest.py")


class CiCertificationTests(unittest.TestCase):
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

    def test_retained_artifacts_are_hashed_and_manifest_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "static.log").write_text("passed\n", encoding="utf-8")
            (root / "manifest.json").write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                {"static.log": sha256(b"passed\n").hexdigest()},
                MANIFEST.file_hashes(root),
            )


if __name__ == "__main__":
    unittest.main()
