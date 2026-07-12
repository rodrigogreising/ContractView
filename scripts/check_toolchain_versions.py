"""Verify supported local tools and exact CI toolchain pins."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def numeric_version(value: str) -> tuple[int, ...]:
    match = re.search(r"(\d+(?:\.\d+)+)", value)
    if not match:
        raise ValueError(f"Cannot parse version from {value!r}")
    return tuple(int(part) for part in match.group(1).split("."))


def main() -> int:
    expected_python = (ROOT / ".python-version").read_text().strip()
    expected_node = (ROOT / ".nvmrc").read_text().strip().lstrip("v")
    actual_python = platform.python_version()
    actual_node_output = subprocess.run(
        ["node", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    actual_node = actual_node_output.lstrip("v")

    failures: list[str] = []
    if not ((3, 12) <= numeric_version(actual_python) < (3, 13)):
        failures.append(f"Python {actual_python} is unsupported; require Python 3.12.x")
    if not ((20, 19) <= numeric_version(actual_node) < (21, 0)):
        failures.append(f"Node {actual_node} is unsupported; require Node 20.19+ and <21")
    if os.environ.get("CI") == "true":
        if actual_python != expected_python:
            failures.append(
                f"CI Python {actual_python} does not match .python-version {expected_python}"
            )
        if actual_node != expected_node:
            failures.append(f"CI Node {actual_node} does not match .nvmrc {expected_node}")

    if failures:
        print("Toolchain version validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        f"Toolchain version validation passed (Python {actual_python}, Node {actual_node})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
