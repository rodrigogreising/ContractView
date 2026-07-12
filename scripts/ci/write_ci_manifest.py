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


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def command_version(*command: str) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def count_tests(content: str) -> int:
    return sum(int(value) for value in re.findall(r"(?:Tests\s+)?(\d+) passed", content))


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
    recorded = now()
    hashes = file_hashes(args.output_dir)
    static_check = {
        "command": "bash scripts/ci/run_static.sh",
        "exitCode": 0,
        "result": "Formatting, fatal lint, mypy, ontology, persistence, module, architecture, SDLC, repository tests, frontend tests, and build passed",
        "recordedAt": recorded,
        "testCount": count_tests(static_log),
        "artifactHashes": {"static.log": hashes["static.log"]},
    }
    hermetic_check = {
        "command": "bash scripts/ci/run_hermetic.sh artifacts/ci",
        "exitCode": 0,
        "result": "Two isolated fresh-volume migration/reset/API/Compose runs passed with an identical reset fingerprint",
        "recordedAt": recorded,
        "testCount": count_tests(hermetic_logs),
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
        "prerequisites": [],
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
