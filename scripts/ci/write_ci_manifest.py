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


def playwright_test_count(result: dict) -> int:
    stats = result.get("stats", {})
    expected = stats.get("expected")
    if not isinstance(expected, int) or expected <= 0:
        raise SystemExit("Journey 12 evidence contains no passing browser test")
    if stats.get("unexpected") != 0 or stats.get("flaky") != 0:
        raise SystemExit("Journey 12 browser evidence is not clean")
    return expected


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


def load_evidence_coverage(issue: str) -> dict[str, object]:
    registry_path = ROOT / "docs/sdlc/issue-evidence-coverage.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    profile = registry.get(issue) if isinstance(registry, dict) else None
    if not isinstance(profile, dict):
        raise SystemExit(f"Evidence coverage is missing for {issue}")
    labels = profile.get("riskAndGateLabels")
    coverage = profile.get("riskCoverage")
    review_skills = profile.get("reviewSkills")
    project_status = profile.get("projectStatus", "Build")
    certification_rationale = profile.get(
        "certificationRationale",
        "Hermetic CI certifies every PR from pinned tools and isolated state, retains exact logs/hashes, and proves consecutive clean reruns are independent.",
    )
    include_journey_in_clean_runtime = profile.get(
        "includeJourneyInCleanRuntime", False
    )
    if (
        not isinstance(labels, list)
        or not labels
        or any(not isinstance(label, str) for label in labels)
        or len(labels) != len(set(labels))
    ):
        raise SystemExit(f"Evidence labels are invalid for {issue}")
    if not isinstance(coverage, dict) or set(coverage) != set(labels):
        raise SystemExit(f"Every risk/gate label must have exact evidence coverage for {issue}")
    if (
        not isinstance(review_skills, list)
        or not review_skills
        or any(
            not isinstance(skill, str) or not skill.startswith("cv-review-")
            for skill in review_skills
        )
        or len(review_skills) != len(set(review_skills))
    ):
        raise SystemExit(f"AI review skills are invalid for {issue}")
    for label, evidence in coverage.items():
        if (
            not isinstance(evidence, list)
            or not evidence
            or any(not isinstance(item, str) or not item.strip() for item in evidence)
        ):
            raise SystemExit(f"Evidence coverage is invalid for {issue} label {label}")
    if project_status not in {
        "Design Review",
        "Build",
        "Evidence Review",
        "Rollout",
        "Completed",
    }:
        raise SystemExit(f"Project status is invalid for {issue}")
    if not isinstance(certification_rationale, str) or not certification_rationale.strip():
        raise SystemExit(f"Certification rationale is invalid for {issue}")
    if not isinstance(include_journey_in_clean_runtime, bool):
        raise SystemExit(f"Clean runtime journey flag is invalid for {issue}")
    return {
        "riskAndGateLabels": labels,
        "riskCoverage": coverage,
        "reviewSkills": review_skills,
        "projectStatus": project_status,
        "certificationRationale": certification_rationale,
        "includeJourneyInCleanRuntime": include_journey_in_clean_runtime,
    }


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
    journey_result_path = args.output_dir / "journey12" / "results.json"
    if not journey_result_path.exists():
        raise SystemExit("Journey 12 browser evidence is missing")
    journey_count = playwright_test_count(json.loads(journey_result_path.read_text()))
    headed_journey_result_path = (
        args.output_dir / "journey12-headed" / "results.json"
    )
    if not headed_journey_result_path.exists():
        raise SystemExit("Paced headed Journey 12 browser evidence is missing")
    headed_journey_count = playwright_test_count(
        json.loads(headed_journey_result_path.read_text())
    )
    evidence_coverage = load_evidence_coverage(issue)
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
        "artifactHashes": {
            name: digest
            for name, digest in hashes.items()
            if name != "static.log"
            and not name.startswith("journey12/")
            and not name.startswith("journey12-headed/")
        },
    }
    journey_check = {
        "command": "bash scripts/run_journey12.sh headless artifacts/ci/journey12",
        "exitCode": 0,
        "result": "Clean Compose Journey 12 passed through normal five-persona login/logout, governed successor activation, and retained video, trace, screenshots, and JSON result",
        "recordedAt": recorded,
        "testCount": journey_count,
        "artifactHashes": {name: digest for name, digest in hashes.items() if name.startswith("journey12/")},
    }
    headed_journey_check = {
        "command": "xvfb-run --auto-servernum bash scripts/run_journey12.sh headed artifacts/ci/journey12-headed",
        "exitCode": 0,
        "result": "Clean Compose Journey 12 passed in default 650 ms paced headed mode with retained video, trace, screenshots, and JSON result",
        "recordedAt": recorded,
        "testCount": headed_journey_count,
        "artifactHashes": {
            name: digest
            for name, digest in hashes.items()
            if name.startswith("journey12-headed/")
        },
    }
    manifest = {
        "issue": issue,
        "projectStatus": evidence_coverage["projectStatus"],
        "branch": args.branch,
        "baseSha": args.base_sha,
        "headSha": args.head_sha,
        "pullRequestUrl": args.pr_url,
        "declaredScope": changed_files(args.base_sha, args.head_sha),
        "recordedAt": recorded,
        "prerequisites": load_prerequisites(issue, args.base_sha),
        "riskAndGateLabels": evidence_coverage["riskAndGateLabels"],
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "node": command_version("node", "--version"),
            "npm": command_version("npm", "--version"),
            "docker": command_version("docker", "--version"),
            "dockerCompose": command_version("docker", "compose", "version"),
        },
        "checks": [
            static_check,
            hermetic_check,
            journey_check,
            headed_journey_check,
        ],
        "certification": {
            "behaviorChanged": True,
            "rationale": evidence_coverage["certificationRationale"],
            "requiredReviewSkills": evidence_coverage["reviewSkills"],
            "evidenceKinds": ["policy", "unit", "integration", "authorization", "boundary", "provenance", "determinism", "migration", "frontend", "compose", "journey", "artifact"],
            "riskCoverage": evidence_coverage["riskCoverage"],
            "cleanRuntimeRequired": True,
            "cleanRuntimeChecks": [
                hermetic_check,
                *(
                    [journey_check, headed_journey_check]
                    if evidence_coverage["includeJourneyInCleanRuntime"]
                    else []
                ),
            ],
        },
        "review": {
            "decision": "Pending",
            "reviewer": "Codex AI",
            "method": "ai",
            "reviewSkills": evidence_coverage["reviewSkills"],
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
