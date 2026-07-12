from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys
import zipfile


HERE = Path(__file__).resolve()
GENERATOR_CANDIDATES = [Path("/app/generate_test_fixtures.py")]
if len(HERE.parents) > 3:
    GENERATOR_CANDIDATES.append(
        HERE.parents[3] / "scripts" / "generate_test_fixtures.py"
    )
GENERATOR_PATH = next(path for path in GENERATOR_CANDIDATES if path.exists())
SPEC = importlib.util.spec_from_file_location("synthetic_fixture_generator", GENERATOR_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)
SOURCE_CANDIDATES = [HERE.parent.parent / "fixtures" / "scenario.json"]
if len(HERE.parents) > 3:
    SOURCE_CANDIDATES.append(
        HERE.parents[3] / "packages" / "test-fixtures" / "scenario.json"
    )
SOURCE = next(path for path in SOURCE_CANDIDATES if path.exists())


def test_fixture_generation_is_byte_identical_and_has_fixed_metadata(tmp_path: Path) -> None:
    roots = [tmp_path / "first", tmp_path / "second"]
    for root in roots:
        root.mkdir()
        shutil.copyfile(SOURCE, root / "scenario.json")
        GENERATOR.generate(root)

    first_files = {
        path.relative_to(roots[0]): path.read_bytes()
        for path in roots[0].rglob("*")
        if path.is_file()
    }
    second_files = {
        path.relative_to(roots[1]): path.read_bytes()
        for path in roots[1].rglob("*")
        if path.is_file()
    }
    assert first_files == second_files

    for name in ("ledger-june-2026.xlsx", "payroll-june-2026.xlsx"):
        with zipfile.ZipFile(roots[0] / "files" / name) as archive:
            metadata = archive.read("docProps/core.xml")
        assert b"2000-01-01T00:00:00Z" in metadata
        assert b"Synthetic Fixture Generator" in metadata
