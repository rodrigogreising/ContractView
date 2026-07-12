"""Validate an issue evidence manifest against the current Git state."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SHA = re.compile(r"^[a-f0-9]{40}$")
DEFAULT_BRANCHES = {"main", "master"}


@dataclass(frozen=True)
class RepositoryState:
    branch: str
    head_sha: str
    tracked_worktree_clean: bool
    changed_files: tuple[str, ...]


def _is_in_scope(path: str, declared_scope: list[str]) -> bool:
    for pattern in declared_scope:
        if pattern.endswith("/") and path.startswith(pattern):
            return True
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def validate_manifest(
    manifest: dict[str, object],
    phase: str,
    state: RepositoryState,
    prerequisite_is_merged: Callable[[str], bool],
) -> list[str]:
    """Return policy failures; an empty list means the evidence is admissible."""

    failures: list[str] = []
    required = {
        "issue",
        "projectStatus",
        "branch",
        "baseSha",
        "headSha",
        "pullRequestUrl",
        "declaredScope",
        "recordedAt",
        "prerequisites",
        "riskAndGateLabels",
        "environment",
        "checks",
        "certification",
        "review",
        "humanApprovalRequirement",
    }
    missing = sorted(required - manifest.keys())
    if missing:
        failures.append("missing required manifest fields: " + ", ".join(missing))
        return failures

    branch = str(manifest["branch"])
    base_sha = str(manifest["baseSha"])
    head_sha = str(manifest["headSha"])
    if branch in DEFAULT_BRANCHES or state.branch in DEFAULT_BRANCHES:
        failures.append("direct work or review on a default branch is prohibited")
    if state.branch != branch:
        failures.append(f"current branch {state.branch!r} does not match manifest branch {branch!r}")
    if not SHA.fullmatch(base_sha) or not SHA.fullmatch(head_sha):
        failures.append("baseSha and headSha must be full lowercase Git SHAs")
    if state.head_sha != head_sha:
        failures.append("review-time mutation detected: current HEAD differs from manifest headSha")
    if not state.tracked_worktree_clean:
        failures.append("review-time mutation detected: tracked worktree is dirty")

    declared_scope = manifest["declaredScope"]
    if not isinstance(declared_scope, list) or not declared_scope:
        failures.append("declaredScope must be a non-empty list")
    else:
        unrelated = [
            path
            for path in state.changed_files
            if not _is_in_scope(path, [str(item) for item in declared_scope])
        ]
        if unrelated:
            failures.append("mixed or undeclared issue scope: " + ", ".join(unrelated))

    prerequisites = manifest["prerequisites"]
    if not isinstance(prerequisites, list):
        failures.append("prerequisites must be a list")
    else:
        for prerequisite in prerequisites:
            if not isinstance(prerequisite, dict):
                failures.append("each prerequisite must be an object")
                continue
            issue = prerequisite.get("issue", "unknown")
            merge_sha = str(prerequisite.get("mergeSha", ""))
            if prerequisite.get("postMergeVerified") is not True:
                failures.append(f"stale prerequisite proof for {issue}: post-merge verification missing")
            if not SHA.fullmatch(merge_sha) or not prerequisite_is_merged(merge_sha):
                failures.append(f"stale prerequisite proof for {issue}: merge is not in origin/master")

    checks = manifest["checks"]
    typed_checks = checks if isinstance(checks, list) else []
    if not isinstance(checks, list) or not checks:
        failures.append("checks must contain machine-readable command results")
    elif any(
        not isinstance(check, dict)
        or not {"command", "exitCode", "result", "recordedAt"}.issubset(check)
        for check in checks
    ):
        failures.append("every check must record command, exitCode, result, and timestamp")
    elif any(check.get("exitCode") != 0 for check in checks):
        failures.append("certification checks must pass; non-zero exitCode recorded")

    raw_labels = manifest["riskAndGateLabels"]
    labels = set(str(label) for label in raw_labels) if isinstance(raw_labels, list) else set()
    certification = manifest["certification"]
    required_review_skills: list[str] = []
    if not isinstance(certification, dict):
        failures.append("certification must be an object")
    else:
        declared_review_skills = certification.get("requiredReviewSkills")
        if (
            not isinstance(declared_review_skills, list)
            or not declared_review_skills
            or any(
                not str(skill).startswith("cv-review-")
                for skill in declared_review_skills
            )
        ):
            failures.append("certification must declare required cv-review-* AI skills")
        else:
            required_review_skills = [str(skill) for skill in declared_review_skills]
        evidence_kinds = certification.get("evidenceKinds")
        if not isinstance(evidence_kinds, list) or not evidence_kinds:
            failures.append("certification must name at least one evidence kind")
            evidence_kinds = []
        test_evidence = {
            "unit",
            "integration",
            "authorization",
            "boundary",
            "provenance",
            "determinism",
            "migration",
            "frontend",
            "compose",
            "journey",
        }
        if test_evidence.intersection(str(kind) for kind in evidence_kinds) and not any(
            isinstance(check, dict) and isinstance(check.get("testCount"), int)
            for check in typed_checks
        ):
            failures.append("test evidence must record an exact testCount")
        if "artifact" in evidence_kinds and not any(
            isinstance(check, dict) and bool(check.get("artifactHashes"))
            for check in typed_checks
        ):
            failures.append("artifact evidence must record artifact hashes")
        risk_coverage = certification.get("riskCoverage")
        if not isinstance(risk_coverage, dict):
            failures.append("certification riskCoverage must be an object")
        else:
            missing_coverage = sorted(
                label
                for label in labels
                if not isinstance(risk_coverage.get(label), list)
                or not risk_coverage[label]
            )
            if missing_coverage:
                failures.append(
                    "risk/gate labels lack executable evidence coverage: "
                    + ", ".join(missing_coverage)
                )
        if certification.get("behaviorChanged") is True:
            behavioral_evidence = {
                "integration",
                "authorization",
                "boundary",
                "provenance",
                "determinism",
                "migration",
                "frontend",
                "compose",
                "journey",
                "artifact",
            }
            if not behavioral_evidence.intersection(str(kind) for kind in evidence_kinds):
                failures.append(
                    "behavior changes require evidence beyond policy or unit checks"
                )
        if certification.get("cleanRuntimeRequired") is True:
            runtime_checks = certification.get("cleanRuntimeChecks")
            if not isinstance(runtime_checks, list) or not runtime_checks:
                failures.append("clean runtime certification is required but missing")
            elif any(
                not isinstance(check, dict) or check.get("exitCode") != 0
                for check in runtime_checks
            ):
                failures.append("clean runtime certification contains a failing check")

    review = manifest["review"]
    if not isinstance(review, dict):
        failures.append("review must be an object")
    else:
        if review.get("reviewedBaseSha") != base_sha or review.get("reviewedHeadSha") != head_sha:
            failures.append("review does not identify the immutable manifest base/head diff")
        if review.get("method") != "ai":
            failures.append("code review must be performed by applicable cv-review AI skills")
        review_skills = review.get("reviewSkills")
        if (
            not isinstance(review_skills, list)
            or not review_skills
            or any(not str(skill).startswith("cv-review-") for skill in review_skills)
        ):
            failures.append("review must name applicable cv-review-* AI skills")
        else:
            missing_reviews = sorted(set(required_review_skills) - set(review_skills))
            if missing_reviews:
                failures.append(
                    "completed review omits required AI reviews: "
                    + ", ".join(missing_reviews)
                )
        if review.get("decision") == "Approved" and review.get("evidenceAdequate") is not True:
            failures.append("Approved AI review requires adequate executable evidence")
        if phase == "done" and review.get("decision") != "Approved":
            failures.append("Done requires an Approved review decision")

    human_approval = manifest["humanApprovalRequirement"]
    if not isinstance(human_approval, dict):
        failures.append("humanApprovalRequirement must be an object")
    elif human_approval.get("required") is True:
        if human_approval.get("decision") != "Approved":
            failures.append("explicitly required human authority approval is missing")
        if not human_approval.get("approver") or not human_approval.get("evidenceUrl"):
            failures.append("required human approval must name approver and evidence URL")

    if phase == "done":
        completion = manifest.get("completion")
        if not isinstance(completion, dict):
            failures.append("Done requires completion evidence")
        else:
            merge_sha = str(completion.get("mergeSha", ""))
            if completion.get("postMergeVerified") is not True:
                failures.append("Done requires successful post-merge verification")
            if not SHA.fullmatch(merge_sha) or not prerequisite_is_merged(merge_sha):
                failures.append("completion mergeSha is not merged into origin/master")
            post_merge_checks = completion.get("postMergeChecks")
            if not isinstance(post_merge_checks, list) or not post_merge_checks:
                failures.append("Done requires machine-readable post-merge checks")

    return failures


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def collect_repository_state(repo: Path, manifest: dict[str, object]) -> RepositoryState:
    base_sha = str(manifest.get("baseSha", ""))
    head_sha = str(manifest.get("headSha", ""))
    changed_files: tuple[str, ...] = ()
    if SHA.fullmatch(base_sha) and SHA.fullmatch(head_sha):
        output = _git(repo, "diff", "--name-only", f"{base_sha}...{head_sha}")
        changed_files = tuple(line for line in output.splitlines() if line)
    return RepositoryState(
        branch=_git(repo, "branch", "--show-current"),
        head_sha=_git(repo, "rev-parse", "HEAD"),
        tracked_worktree_clean=not bool(
            _git(repo, "status", "--porcelain", "--untracked-files=no")
        ),
        changed_files=changed_files,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--phase", choices=("review", "done"), required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Evidence validation failed: cannot read manifest: {error}")
        return 1

    repo = args.repo.resolve()
    state = collect_repository_state(repo, manifest)

    def is_merged(sha: str) -> bool:
        return subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "origin/master"],
            cwd=repo,
            capture_output=True,
        ).returncode == 0

    failures = validate_manifest(manifest, args.phase, state, is_merged)
    if failures:
        print("Evidence validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Evidence validation passed for {manifest['issue']} at {manifest['headSha']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
