"""Build and verify a neutral, history-free public repository candidate."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile
import zlib


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_TITLE = "Synthetic Reimbursement Workflow POC"
PUBLIC_SLUG = "synthetic-reimbursement-workflow-poc"
PUBLIC_IDENTIFIER = "synthetic_reimbursement_poc"
INCLUDED_PREFIXES = (
    "apps/",
    "docs/adr/",
    "docs/architecture/",
    "docs/journeys/",
    "packages/",
    "services/",
)
INCLUDED_PATHS = {
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "LICENSE",
    "Makefile",
    "README.md",
    "SECURITY.md",
    "compose.publication.yaml",
    "compose.yaml",
    "package.json",
    "scripts/check_module_boundaries.py",
    "scripts/check_persistence_statements.py",
    "scripts/check_shared_contracts.py",
    "scripts/generate_shared_contracts.py",
    "scripts/generate_test_fixtures.py",
    "scripts/tests/test_module_boundaries.py",
    "scripts/tests/test_shared_contracts.py",
}
EXCLUDED_PUBLIC_PATHS = {
    "docs/architecture/poc-boundary-review.md",
}
TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
LEGACY_FRAGMENTS = (
    "shoken",
    "contractview",
    "seaofmachines",
    "viaadsolem",
    "rodrigogreising",
    "linear.app",
    "metro human services agency",
    "harbor community services",
    "metro oversight office",
    "metro property services",
    "northstar learning supply",
    "civic equipment rental",
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)")
PRIVATE_REFERENCE_PATTERNS = (
    re.compile(r"\bSUB-[0-9]+\b"),
    re.compile(r"\bREC-[0-9]+\b"),
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def included(path: str) -> bool:
    return (
        path not in EXCLUDED_PUBLIC_PATHS
        and (path in INCLUDED_PATHS or path.startswith(INCLUDED_PREFIXES))
    )


def public_path(path: str) -> str:
    return path.replace("contractview", PUBLIC_IDENTIFIER)


def neutralize(content: str) -> str:
    neutral = (
        content.replace("ContractView", PUBLIC_TITLE)
        .replace("CONTRACTVIEW", "SYNTHETIC_REIMBURSEMENT_POC")
        .replace("contractview", PUBLIC_IDENTIFIER)
    )
    neutral = (
        neutral.replace(f"@{PUBLIC_IDENTIFIER}", f"@{PUBLIC_SLUG}")
        .replace(
            f"{PUBLIC_IDENTIFIER}-artifacts",
            "synthetic-reimbursement-poc-artifacts",
        )
    )
    neutral = re.sub(r"\bSUB-[0-9]+\b", "implementation milestone", neutral)
    return re.sub(r"\bREC-[0-9]+\b", "recovery milestone", neutral)


def binary_text(path: Path) -> str:
    if path.suffix == ".pdf":
        page_text = subprocess.run(
            ["pdftotext", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        metadata = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return page_text + "\n" + metadata
    if path.suffix == ".xlsx":
        with zipfile.ZipFile(path) as archive:
            return "\n".join(
                archive.read(name).decode("utf-8", errors="replace")
                for name in sorted(archive.namelist())
                if name.endswith(".xml")
            )
    if path.suffix == ".png":
        content = path.read_bytes()
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise SystemExit(f"Invalid PNG fixture: {path}")
        offset = 8
        values: list[str] = []
        while offset < len(content):
            length = struct.unpack(">I", content[offset : offset + 4])[0]
            kind = content[offset + 4 : offset + 8]
            data = content[offset + 8 : offset + 8 + length]
            offset += 12 + length
            if kind == b"tEXt":
                values.append(data.decode("latin-1", errors="replace"))
            elif kind == b"zTXt" and b"\x00" in data:
                _, compressed = data.split(b"\x00", 1)
                values.append(zlib.decompress(compressed[1:]).decode("latin-1"))
            elif kind == b"iTXt":
                values.append(data.decode("utf-8", errors="replace"))
        return "\n".join(values)
    return ""


def verify_text(path: Path, content: str, failures: list[str]) -> None:
    lowered = content.lower()
    for fragment in LEGACY_FRAGMENTS:
        if fragment in lowered:
            failures.append(f"{path}: contains blocked legacy/private fragment")
    for pattern in SECRET_PATTERNS:
        if pattern.search(content):
            failures.append(f"{path}: contains a high-confidence secret shape")
    for pattern in PRIVATE_REFERENCE_PATTERNS:
        if pattern.search(content):
            failures.append(f"{path}: contains a private control-plane reference")
    for match in EMAIL.finditer(content):
        domain = match.group(1).lower()
        if not (
            domain.endswith(".test")
            or domain == "example.test"
            or domain == "localhost"
        ):
            failures.append(f"{path}: contains non-reserved email domain {domain}")


def build(output: Path, source_sha: str) -> dict:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    included_paths: list[str] = []
    excluded_count = 0
    for relative in tracked_files():
        if not included(relative):
            excluded_count += 1
            continue
        source = ROOT / relative
        destination_relative = public_path(relative)
        destination = output / destination_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in TEXT_SUFFIXES or source.name in {
            ".env.example",
            ".gitignore",
            ".nvmrc",
            ".python-version",
            "LICENSE",
            "Makefile",
        }:
            destination.write_text(
                neutralize(source.read_text(encoding="utf-8")), encoding="utf-8"
            )
        else:
            shutil.copyfile(source, destination)
        included_paths.append(destination_relative)

    failures: list[str] = []
    hashes: dict[str, str] = {}
    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        relative = str(path.relative_to(output))
        verify_text(Path(relative), relative, failures)
        if ".git" in path.parts:
            failures.append(f"{relative}: Git metadata is prohibited")
        if path.suffix in TEXT_SUFFIXES or path.name in {
            ".env.example",
            ".gitignore",
            "LICENSE",
            "Makefile",
        }:
            verify_text(path, path.read_text(encoding="utf-8"), failures)
        else:
            extracted = binary_text(path)
            if extracted:
                verify_text(path, extracted, failures)
        hashes[relative] = sha256(path.read_bytes()).hexdigest()

    if failures:
        raise SystemExit("Publication candidate rejected:\n- " + "\n- ".join(failures))
    manifest = {
        "schemaVersion": "1.0.0",
        "candidateTitle": PUBLIC_TITLE,
        "repositorySlug": PUBLIC_SLUG,
        "sourceSha": source_sha,
        "gitHistoryIncluded": False,
        "privateControlPlaneIncluded": False,
        "includedPaths": sorted(included_paths),
        "exclusionRules": [
            "Only root files named by the publication allowlist",
            "apps/**, packages/**, and services/**",
            "docs/adr/**, docs/architecture/**, and docs/journeys/** except private boundary review evidence",
            "Only explicitly named architecture, contract-generation, and fixture-generation scripts",
            "No Git metadata, agent skills, SDLC control-plane evidence, local artifacts, caches, or publication tooling",
        ],
        "excludedSourceFileCount": excluded_count,
        "fileHashes": hashes,
        "structuralChecks": [
            {"name": "legacy-and-private-fragments", "exitCode": 0},
            {"name": "high-confidence-secret-shapes", "exitCode": 0},
            {"name": "reserved-email-domains", "exitCode": 0},
            {"name": "binary-content-and-metadata", "exitCode": 0},
            {"name": "history-and-control-plane-exclusion", "exitCode": 0},
        ],
        "requiredCertificationCommands": [
            "python -m unittest scripts.tests.test_module_boundaries scripts.tests.test_shared_contracts",
            "python -m pytest -q services/api-workflow/tests",
            "npm --prefix apps/web-app test",
            "npm --prefix apps/web-app run build",
            "docker compose -f compose.yaml -f compose.publication.yaml build",
            "docker compose -f compose.yaml -f compose.publication.yaml up -d",
            "docker compose -f compose.yaml -f compose.publication.yaml exec -T api python -m app.manage reset",
            "docker compose -f compose.yaml -f compose.publication.yaml exec -T api pytest -q",
        ],
        "certificationStatus": "pending",
        "rightsPolicy": "all-rights-reserved",
        "visibilityChanged": False,
    }
    manifest_path = output / "PUBLICATION-MANIFEST.json"
    manifest_text = json.dumps(manifest, indent=2) + "\n"
    verify_text(manifest_path, manifest_text, failures)
    if failures:
        raise SystemExit("Publication candidate rejected:\n- " + "\n- ".join(failures))
    manifest_path.write_text(manifest_text, encoding="utf-8")
    print(
        f"Built structurally verified candidate with {len(hashes)} files at {output}"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-sha")
    args = parser.parse_args()
    source_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if status:
        raise SystemExit("Publication export requires a clean Git worktree")
    if args.source_sha and args.source_sha != source_sha:
        raise SystemExit(
            f"Requested source SHA {args.source_sha} does not match HEAD {source_sha}"
        )
    build(args.output.resolve(), source_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
