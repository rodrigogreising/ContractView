"""Repository-wide deterministic text and structured-file format checks."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".css", ".html", ".json", ".md", ".py", ".sql", ".ts", ".tsx", ".yaml", ".yml"}
SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "artifacts",
    "dist",
    "node_modules",
    "tmp",
}


def main() -> int:
    failures: list[str] = []
    checked = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if SKIP_PARTS.intersection(path.relative_to(ROOT).parts):
            continue
        checked += 1
        relative = path.relative_to(ROOT)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"{relative}: not valid UTF-8")
            continue
        if content and not content.endswith("\n"):
            failures.append(f"{relative}: missing final newline")
        for number, line in enumerate(content.splitlines(), start=1):
            if line != line.rstrip():
                failures.append(f"{relative}:{number}: trailing whitespace")
            if "\t" in line and path.suffix != ".md":
                failures.append(f"{relative}:{number}: tab character")
        if path.suffix == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as error:
                failures.append(f"{relative}: invalid JSON: {error}")
    if failures:
        print("Formatting validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Formatting validation passed ({checked} UTF-8 structured/text files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
