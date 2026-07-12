"""Build and schema-validate the durable GitHub CI evidence manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import re
import subprocess
from typing import Callable

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
REVIEW_SKILLS = [
    "cv-review-adr-architecture",
    "cv-review-boundary-review",
    "cv-review-security-privacy",
    "cv-review-requirements-traceability",
    "cv-review-implementation-tests",
    "cv-review-journey-certification",
    "cv-review-release-readiness",
]
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SHA = re.compile(r"^[a-f0-9]{40}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def command_version(*command: str) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def count_tests(content: str) -> int:
    normalized = ANSI_ESCAPE.sub("", content)
    pytest_counts = re.findall(
        r"(?m)^\s*(\d+) passed(?: in [0-9.]+s)?\s*$", normalized
    )
    vitest_counts = re.findall(
        r"(?m)^\s*Tests\s+(\d+) passed(?:\s+\(\d+\))?\s*$", normalized
    )
    return sum(int(value) for value in [*pytest_counts, *vitest_counts])


def required_test_count(label: str, content: str) -> int:
    count = count_tests(content)
    if count <= 0:
        raise SystemExit(f"{label} evidence contains no passing test count")
    return count


def file_hashes(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }


def changed_files(base_sha: str, head_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = [line for line in result.stdout.splitlines() if line]
    if not paths:
        raise SystemExit("The PR base/head diff has no changed files")
    return paths


def validate_prerequisites(
    issue: str,
    registry: object,
    prerequisite_is_merged: Callable[[str], bool],
) -> list[dict[str, object]]:
    if not isinstance(registry, dict):
        raise SystemExit("Issue prerequisite registry must be an object")
    prerequisites = registry.get(issue, [])
    if not isinstance(prerequisites, list):
        raise SystemExit(f"Prerequisites for {issue} must be a list")
    validated: list[dict[str, object]] = []
    for prerequisite in prerequisites:
        if not isinstance(prerequisite, dict):
            raise SystemExit(f"Prerequisites for {issue} must contain objects")
        blocker = prerequisite.get("issue")
        merge_sha = prerequisite.get("mergeSha")
        if not isinstance(blocker, str) or not re.fullmatch(r"SUB-[0-9]+", blocker):
            raise SystemExit(f"Prerequisite for {issue} has an invalid issue identifier")
        if not isinstance(merge_sha, str) or not SHA.fullmatch(merge_sha):
            raise SystemExit(f"Prerequisite {blocker} has an invalid merge SHA")
        if prerequisite.get("postMergeVerified") is not True:
            raise SystemExit(f"Prerequisite {blocker} lacks post-merge verification")
        if not prerequisite_is_merged(merge_sha):
            raise SystemExit(
                f"Prerequisite {blocker} merge {merge_sha} is not an ancestor of the PR base"
            )
        validated.append(
            {
                "issue": blocker,
                "mergeSha": merge_sha,
                "postMergeVerified": True,
            }
        )
    return validated


def load_prerequisites(issue: str, base_sha: str) -> list[dict[str, object]]:
    registry_path = ROOT / "docs/sdlc/issue-prerequisites.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    def is_merged(merge_sha: str) -> bool:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", merge_sha, base_sha],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    return validate_prerequisites(issue, registry, is_merged)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--pr-url", required=True)
    args = parser.parse_args()
    issue_match = re.search(r"(?:^|/)(sub-\d+)(?:-|$)", args.branch, re.I)
    if not issue_match:
        raise SystemExit(f"Cannot derive Linear issue from branch {args.branch!r}")
    issue = issue_match.group(1).upper()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    static_log = (args.output_dir / "static.log").read_text(encoding="utf-8")
    hermetic_logs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(args.output_dir.glob("api-pass-*.log"))
    )
    reset_fingerprint = (args.output_dir / "reset-fingerprint.sha256").read_text().strip()
    recorded = now()
    hashes = file_hashes(args.output_dir)
    static_check = {
        "command": "bash scripts/ci/run_static.sh",
        "exitCode": 0,
        "result": "Formatting, fatal lint, mypy, ontology, persistence, module, architecture, SDLC, repository tests, frontend tests, and build passed",
        "recordedAt": recorded,
        "testCount": required_test_count("Static", static_log),
        "artifactHashes": {"static.log": hashes["static.log"]},
    }
    hermetic_check = {
        "command": "bash scripts/ci/run_hermetic.sh artifacts/ci",
        "exitCode": 0,
        "result": f"Two isolated fresh-volume migration/reset/API/Compose runs passed with identical reset fingerprint {reset_fingerprint}",
        "recordedAt": recorded,
        "testCount": required_test_count("Hermetic", hermetic_logs),
        "artifactHashes": {name: digest for name, digest in hashes.items() if name != "static.log"},
    }
    manifest = {
        "issue": issue,
        "projectStatus": "Build",
        "branch": args.branch,
        "baseSha": args.base_sha,
        "headSha": args.head_sha,
        "pullRequestUrl": args.pr_url,
        "declaredScope": changed_files(args.base_sha, args.head_sha),
        "recordedAt": recorded,
        "prerequisites": load_prerequisites(issue, args.base_sha),
        "riskAndGateLabels": ["gate:release-certification"],
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "node": command_version("node", "--version"),
            "npm": command_version("npm", "--version"),
            "docker": command_version("docker", "--version"),
            "dockerCompose": command_version("docker", "compose", "version"),
        },
        "checks": [static_check, hermetic_check],
        "certification": {
            "behaviorChanged": True,
            "rationale": "Hermetic CI certifies every PR from pinned tools and isolated state, retains exact logs/hashes, and proves consecutive clean reruns are independent.",
            "requiredReviewSkills": REVIEW_SKILLS,
            "evidenceKinds": ["policy", "unit", "integration", "boundary", "migration", "frontend", "compose", "artifact"],
            "riskCoverage": {
                "gate:release-certification": [
                    "Pinned format/lint/type/test/build gates",
                    "Two isolated Compose reruns with equal reset fingerprints",
                    "Uploaded manifest and hashed command logs",
                ]
            },
            "cleanRuntimeRequired": True,
            "cleanRuntimeChecks": [hermetic_check],
        },
        "review": {
            "decision": "Pending",
            "reviewer": "Codex AI",
            "method": "ai",
            "reviewSkills": REVIEW_SKILLS,
            "reviewedBaseSha": args.base_sha,
            "reviewedHeadSha": args.head_sha,
            "evidenceAdequate": False,
            "findings": [],
        },
        "humanApprovalRequirement": {
            "required": False,
            "basis": "CI and code review use executable evidence plus AI review; human certification is reserved for staging or production promotion.",
        },
    }
    schema = json.loads((ROOT / "docs/sdlc/evidence-manifest.schema.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)
    output = args.output_dir / "manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote schema-valid CI evidence manifest for {issue}: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
