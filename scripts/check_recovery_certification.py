"""Validate the durable SUB-66 recovery certification record."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "docs/sdlc/recovery/SUB-66-recovery-certification.json"
SHA = re.compile(r"^[a-f0-9]{40}$")

LEGACY_DONE = {
    "SUB-18", "SUB-19", "SUB-20", "SUB-23", "SUB-24", "SUB-25",
    "SUB-27", "SUB-28", "SUB-30", "SUB-31", "SUB-32", "SUB-33",
    "SUB-34", "SUB-35", "SUB-36", "SUB-37", "SUB-38", "SUB-39",
    "SUB-40", "SUB-41", "SUB-43", "SUB-44", "SUB-45", "SUB-47",
}
RECOVERY_DONE = {
    "SUB-57", "SUB-58", "SUB-59", "SUB-60", "SUB-61", "SUB-62",
    "SUB-63", "SUB-64", "SUB-65", "SUB-67", "SUB-68", "SUB-69",
    "SUB-79",
}
REQUIRED_PREREQUISITES = {
    "SUB-58", "SUB-59", "SUB-60", "SUB-61", "SUB-62", "SUB-63",
    "SUB-64", "SUB-65", "SUB-67", "SUB-68",
}
CONTINUATION_ISSUES = {"SUB-26", "SUB-50", "SUB-53", "SUB-55"}


def _objects(value: object) -> list[dict[str, object]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def validate_record(
    record: dict[str, object],
    root: Path,
    merge_is_ancestor: Callable[[str], bool],
) -> list[str]:
    failures: list[str] = []
    required = {
        "schemaVersion", "issue", "baselineSha", "projectStatus", "decision",
        "decisionScope", "auditSnapshot", "recoveryPrerequisites",
        "historicalDoneAudit", "invalidatedClaims", "exceptions",
        "continuationGate", "humanApprovalRequirement",
    }
    missing = sorted(required - record.keys())
    if missing:
        return ["missing required fields: " + ", ".join(missing)]

    if record["issue"] != "SUB-66" or record["projectStatus"] != "Evidence Review":
        failures.append("record must be controlled by SUB-66 in Evidence Review")
    if record["decision"] != "Certified with exceptions":
        failures.append("recovery decision must be Certified with exceptions")
    if not SHA.fullmatch(str(record["baselineSha"])):
        failures.append("baselineSha must be a full lowercase Git SHA")

    audit = _objects(record["historicalDoneAudit"])
    expected = LEGACY_DONE | RECOVERY_DONE
    identifiers = [str(item.get("issue", "")) for item in audit]
    if len(audit) != len(expected) or set(identifiers) != expected:
        failures.append("historical Done audit must cover exactly the 37 recorded issues")
    if len(identifiers) != len(set(identifiers)):
        failures.append("historical Done audit contains duplicate issues")

    snapshot = record["auditSnapshot"]
    if not isinstance(snapshot, dict) or snapshot.get("doneIssueCount") != len(expected):
        failures.append("auditSnapshot must record the exact Done issue count")

    for item in audit:
        issue = str(item.get("issue", ""))
        if item.get("status") != "Done" or item.get("statusPreserved") is not True:
            failures.append(f"{issue}: historical Done status is not explicitly preserved")
        evidence = item.get("evidencePaths")
        if not isinstance(evidence, list) or not evidence:
            failures.append(f"{issue}: durable evidence paths are missing")
        else:
            for raw_path in evidence:
                if not (root / str(raw_path)).is_file():
                    failures.append(f"{issue}: missing evidence path {raw_path}")
        if issue in LEGACY_DONE:
            if item.get("approvalDisposition") != "invalidated":
                failures.append(f"{issue}: provisional legacy approval must be invalidated")
            superseded = item.get("supersededBy")
            if (
                not isinstance(superseded, list)
                or not superseded
                or not set(str(value) for value in superseded).issubset(RECOVERY_DONE)
            ):
                failures.append(f"{issue}: superseding recovery issues are missing or invalid")
        elif issue in RECOVERY_DONE:
            merge_sha = str(item.get("mergeSha", ""))
            if not SHA.fullmatch(merge_sha) or not merge_is_ancestor(merge_sha):
                failures.append(f"{issue}: recovery merge is not in origin/master")
            if item.get("postMergeVerified") is not True:
                failures.append(f"{issue}: post-merge verification is missing")
            if not str(item.get("pullRequestUrl", "")).startswith("https://github.com/"):
                failures.append(f"{issue}: pull request URL is missing")

    prerequisites = _objects(record["recoveryPrerequisites"])
    if {str(item.get("issue", "")) for item in prerequisites} != REQUIRED_PREREQUISITES:
        failures.append("recoveryPrerequisites do not match the SUB-66 blocker set")
    for item in prerequisites:
        issue = str(item.get("issue", ""))
        merge_sha = str(item.get("mergeSha", ""))
        if item.get("postMergeVerified") is not True:
            failures.append(f"{issue}: prerequisite lacks post-merge proof")
        if not SHA.fullmatch(merge_sha) or not merge_is_ancestor(merge_sha):
            failures.append(f"{issue}: prerequisite merge is not in origin/master")

    claims = _objects(record["invalidatedClaims"])
    if not claims or any(
        not {"claim", "disposition", "reason", "replacementEvidence"}.issubset(item)
        or item.get("disposition") != "invalidated"
        for item in claims
    ):
        failures.append("invalidatedClaims must explicitly name claims, reasons, and replacements")

    exceptions = _objects(record["exceptions"])
    exception_fields = {
        "id", "owner", "risk", "compensatingControl", "targetResolution", "pocImpact"
    }
    if not exceptions or any(not exception_fields.issubset(item) for item in exceptions):
        failures.append("every exception must record owner, risk, control, target, and POC impact")

    gate = record["continuationGate"]
    if not isinstance(gate, dict):
        failures.append("continuationGate must be an object")
    else:
        if set(str(value) for value in gate.get("issues", [])) != CONTINUATION_ISSUES:
            failures.append("continuationGate must cover SUB-26, SUB-50, SUB-53, and SUB-55")
        if gate.get("state") != "blocked-until-sub-66-merge-verification":
            failures.append("continuation issues cannot be unblocked before SUB-66 merge verification")

    human = record["humanApprovalRequirement"]
    if not isinstance(human, dict) or human.get("developmentIntegrationRequired") is not False:
        failures.append("development integration must use executable evidence and AI review")
    if not isinstance(human, dict) or human.get("stagingProductionPromotionRequired") is not True:
        failures.append("staging/production promotion must retain explicit human authority")
    return failures


def _merged_in_origin_master(sha: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "origin/master"],
        cwd=ROOT,
        capture_output=True,
    ).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Recovery certification validation failed: {error}")
        return 1
    failures = validate_record(record, ROOT, _merged_in_origin_master)
    if failures:
        print("Recovery certification validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "Recovery certification validation passed "
        f"({len(record['historicalDoneAudit'])} Done issues, "
        f"{len(record['recoveryPrerequisites'])} merged prerequisites)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
