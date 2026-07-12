"""Capture and validate a sanitized GitHub branch-protection evidence record."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sanitize_and_validate(
    payload: object,
    repository: str,
    branch: str,
    required_context: str,
) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise SystemExit("GitHub branch-protection response must be an object")
    status_checks = payload.get("required_status_checks")
    enforce_admins = payload.get("enforce_admins")
    force_pushes = payload.get("allow_force_pushes")
    deletions = payload.get("allow_deletions")
    if not isinstance(status_checks, dict):
        raise SystemExit("Branch protection lacks required status checks")
    contexts = status_checks.get("contexts")
    if not isinstance(contexts, list) or required_context not in contexts:
        raise SystemExit(f"Branch protection does not require {required_context!r}")
    if status_checks.get("strict") is not True:
        raise SystemExit("Branch protection must require an up-to-date branch")
    if not isinstance(enforce_admins, dict) or enforce_admins.get("enabled") is not True:
        raise SystemExit("Branch protection must enforce required checks for administrators")
    if not isinstance(force_pushes, dict) or force_pushes.get("enabled") is not False:
        raise SystemExit("Branch protection must prohibit force pushes")
    if not isinstance(deletions, dict) or deletions.get("enabled") is not False:
        raise SystemExit("Branch protection must prohibit deletion")
    return {
        "repository": repository,
        "branch": branch,
        "recordedAt": now(),
        "requiredStatusChecks": {
            "strict": True,
            "contexts": sorted(str(context) for context in contexts),
        },
        "enforceAdmins": True,
        "allowForcePushes": False,
        "allowDeletions": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", default="master")
    parser.add_argument("--required-context", default="certification")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    response = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{args.repository}/branches/{args.branch}/protection",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    record = sanitize_and_validate(
        json.loads(response.stdout),
        args.repository,
        args.branch,
        args.required_context,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote valid sanitized branch-protection evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
