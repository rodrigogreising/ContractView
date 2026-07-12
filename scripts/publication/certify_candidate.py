"""Execute and retain full certification evidence for a publication candidate."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess


ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def run(command: list[str], cwd: Path) -> tuple[str, str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if result.returncode:
        raise SystemExit(
            f"Certification command failed ({result.returncode}): {' '.join(command)}\n{output}"
        )
    return " ".join(command), output


def count_pytest(output: str) -> int:
    normalized = ANSI.sub("", output)
    matches = re.findall(r"(?m)^\s*(\d+) passed(?: in [0-9.]+s)?\s*$", normalized)
    if len(matches) != 1:
        raise SystemExit(f"Expected one pytest count, found {matches}")
    return int(matches[0])


def count_vitest(output: str) -> int:
    normalized = ANSI.sub("", output)
    matches = re.findall(
        r"(?m)^\s*Tests\s+(\d+) passed(?:\s+\(\d+\))?\s*$", normalized
    )
    if len(matches) != 1:
        raise SystemExit(f"Expected one Vitest count, found {matches}")
    return int(matches[0])


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_source_hashes(candidate: Path, manifest: dict) -> None:
    expected = manifest.get("fileHashes")
    if not isinstance(expected, dict) or not expected:
        raise SystemExit("Publication manifest has no source file hashes")
    actual = {
        relative: digest(candidate / relative)
        for relative in expected
        if (candidate / relative).is_file()
    }
    missing = sorted(set(expected) - set(actual))
    changed = sorted(
        relative
        for relative, expected_digest in expected.items()
        if actual.get(relative) != expected_digest
    )
    actual_paths = {
        str(path.relative_to(candidate))
        for path in candidate.rglob("*")
        if path.is_file() and path.name != "PUBLICATION-MANIFEST.json"
    }
    unexpected = sorted(actual_paths - set(expected))
    if missing or changed or unexpected:
        raise SystemExit(
            "Candidate differs from its manifest; "
            f"missing={missing}, changed={changed}, unexpected={unexpected}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--project", default="publication-certification")
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    manifest_path = candidate / "PUBLICATION-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_source_hashes(candidate, manifest)
    evidence = (
        args.evidence.resolve()
        if args.evidence
        else candidate.parent / f"{candidate.name}-certification"
    )
    if evidence.exists():
        shutil.rmtree(evidence)
    evidence.mkdir(parents=True)
    compose = [
        "docker",
        "compose",
        "-p",
        args.project,
        "-f",
        "compose.yaml",
        "-f",
        "compose.publication.yaml",
    ]
    checks: list[dict] = []
    try:
        run([*compose, "down", "-v", "--remove-orphans"], candidate)
        command, build_output = run(
            [*compose, "up", "-d", "--build", "postgres", "minio", "api", "web"],
            candidate,
        )
        build_log = evidence / "compose-build.log"
        build_log.write_text(build_output, encoding="utf-8")
        checks.append(
            {
                "command": command,
                "exitCode": 0,
                "result": "Fresh isolated services built and became healthy",
                "artifactHashes": {build_log.name: digest(build_log)},
            }
        )
        reset_command, reset_output = run(
            [*compose, "exec", "-T", "api", "python", "-m", "app.manage", "reset"],
            candidate,
        )
        reset_log = evidence / "reset.log"
        reset_log.write_text(reset_output, encoding="utf-8")
        checks.append(
            {
                "command": reset_command,
                "exitCode": 0,
                "result": "Numbered migrations and deterministic synthetic reset passed",
                "artifactHashes": {reset_log.name: digest(reset_log)},
            }
        )
        api_command, api_output = run(
            [*compose, "exec", "-T", "api", "pytest", "-q"], candidate
        )
        api_log = evidence / "api-tests.log"
        api_log.write_text(api_output, encoding="utf-8")
        checks.append(
            {
                "command": api_command,
                "exitCode": 0,
                "result": "Complete API and fixture regression passed",
                "testCount": count_pytest(api_output),
                "artifactHashes": {api_log.name: digest(api_log)},
            }
        )
        web_command, web_output = run([*compose, "run", "--rm", "web-test"], candidate)
        web_log = evidence / "frontend-tests.log"
        web_log.write_text(web_output, encoding="utf-8")
        checks.append(
            {
                "command": web_command,
                "exitCode": 0,
                "result": "Clean npm install, production build, and frontend tests passed",
                "testCount": count_vitest(web_output),
                "artifactHashes": {web_log.name: digest(web_log)},
            }
        )
        _, service_output = run([*compose, "ps", "--format", "json"], candidate)
        service_log = evidence / "compose-services.jsonl"
        service_log.write_text(service_output, encoding="utf-8")
        checks.append(
            {
                "command": " ".join([*compose, "ps", "--format", "json"]),
                "exitCode": 0,
                "result": "PostgreSQL, MinIO, API, and web service state retained",
                "artifactHashes": {
                    service_log.name: digest(service_log)
                },
            }
        )
    finally:
        subprocess.run(
            [*compose, "down", "-v", "--remove-orphans"],
            cwd=candidate,
            capture_output=True,
            text=True,
        )

    manifest["certificationStatus"] = "passed"
    manifest["certification"] = {
        "environment": {
            "platform": platform.platform(),
            "docker": subprocess.run(
                ["docker", "--version"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "dockerCompose": subprocess.run(
                ["docker", "compose", "version"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
        },
        "checks": checks,
        "evidenceIncludedInCandidate": False,
        "evidenceRetention": "Private sibling evidence bundle; hashes retained here",
        "visibilityChanged": False,
        "ownerPublicationDecision": "pending",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"Certified candidate: {checks[2]['testCount']} API tests and "
        f"{checks[3]['testCount']} frontend tests passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
