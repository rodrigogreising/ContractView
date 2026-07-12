"""Fail when ContractView's isolated delivery controls drift out of sync."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(text: str, needle: str, source: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{source}: missing {needle!r}")


def main() -> int:
    failures: list[str] = []

    agents = read("AGENTS.md")
    for needle in (
        "## Immutable Delivery Protocol",
        "`Backlog` -> `Todo` -> `In Progress` -> `In Review` -> `Done`",
        "docs/codex/review-preflight.md",
        "docs/sdlc/evidence-manifest.schema.json",
    ):
        require(agents, needle, "AGENTS.md", failures)

    preflight = read("docs/codex/review-preflight.md")
    for needle in (
        "## Blocking Conditions",
        "immutable base/head diff",
        "Do not edit",
        "Applicable AI review skills plus",
        "Human code review is not a default gate.",
        "Move the issue to `Done` only after post-merge verification passes.",
    ):
        require(preflight, needle, "docs/codex/review-preflight.md", failures)

    schema_path = ROOT / "docs/sdlc/evidence-manifest.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"{schema_path.relative_to(ROOT)}: invalid JSON: {error}")
    else:
        required = set(schema.get("required", []))
        expected = {
            "issue",
            "branch",
            "baseSha",
            "headSha",
            "pullRequestUrl",
            "declaredScope",
            "recordedAt",
            "prerequisites",
            "riskAndGateLabels",
            "checks",
            "certification",
            "review",
            "humanApprovalRequirement",
        }
        missing = sorted(expected - required)
        if missing:
            failures.append(
                "docs/sdlc/evidence-manifest.schema.json: missing required fields "
                + ", ".join(missing)
            )
        certification_properties = (
            schema.get("properties", {})
            .get("certification", {})
            .get("properties", {})
        )
        if "requiredReviewSkills" not in certification_properties:
            failures.append(
                "docs/sdlc/evidence-manifest.schema.json: missing requiredReviewSkills"
            )

    review_skills = sorted((ROOT / ".agents/skills").glob("cv-review-*/SKILL.md"))
    if len(review_skills) != 10:
        failures.append(f"expected 10 cv-review skills, found {len(review_skills)}")
    for path in review_skills:
        relative = str(path.relative_to(ROOT))
        content = path.read_text(encoding="utf-8")
        for needle in (
            "docs/codex/review-preflight.md",
            "## Immutable Review Preflight",
            "Return `Blocked`",
            "Do not edit during the review pass.",
            "This skill is an AI code reviewer.",
            "issue-proportionate executable certification",
            "Human code review is not required;",
            "reviewed base and head SHAs",
        ):
            require(content, needle, relative, failures)

    executor = read(".agents/skills/cv-execute-linear-backlog/SKILL.md")
    for needle in (
        "docs/codex/review-preflight.md",
        "docs/sdlc/evidence-manifest.schema.json",
        "Do not implement directly on `master`.",
        "Do not combine multiple leaf issues in one PR",
        "Treat every applicable `cv-review-*` skill as an AI code reviewer.",
        "Do not move issues to `Done` before merge and post-merge verification.",
    ):
        require(executor, needle, ".agents/skills/cv-execute-linear-backlog/SKILL.md", failures)

    workflow = read("docs/sdlc/linear-workflow.md")
    for needle in (
        "| `Backlog` |",
        "| `Todo` |",
        "| `In Progress` |",
        "| `In Review` |",
        "| `Done` |",
        "merged prerequisite",
    ):
        require(workflow, needle, "docs/sdlc/linear-workflow.md", failures)

    for relative in (
        "scripts/validate_delivery_evidence.py",
        "scripts/tests/test_delivery_evidence.py",
    ):
        if not (ROOT / relative).is_file():
            failures.append(f"{relative}: missing executable delivery-policy evidence")

    ci_workflow = read(".github/workflows/contractview-ci.yml")
    for needle in (
        "runs-on: ubuntu-24.04",
        "python-version-file: .python-version",
        "node-version-file: .nvmrc",
        "bash scripts/ci/run_static.sh",
        "bash scripts/ci/run_hermetic.sh artifacts/ci",
        "python3 scripts/ci/write_ci_manifest.py",
        "retention-days: 30",
    ):
        require(needle=needle, text=ci_workflow, source=".github/workflows/contractview-ci.yml", failures=failures)
    action_uses = [line.strip() for line in ci_workflow.splitlines() if "uses: actions/" in line]
    for action_use in action_uses:
        reference = action_use.split("@", 1)[-1].split()[0]
        if len(reference) != 40 or any(character not in "0123456789abcdef" for character in reference):
            failures.append(
                ".github/workflows/contractview-ci.yml: official actions must use immutable commit SHAs"
            )

    for relative, version_expected in (
        (".python-version", "3.12.13"),
        (".nvmrc", "20.20.2"),
    ):
        if read(relative).strip() != version_expected:
            failures.append(f"{relative}: expected exact toolchain pin {version_expected}")

    for relative in (
        "services/api-workflow/Dockerfile",
        "apps/web-app/Dockerfile",
        "compose.yaml",
    ):
        for line in read(relative).splitlines():
            stripped = line.strip()
            if (stripped.startswith("FROM ") or stripped.startswith("image:")) and "@sha256:" not in stripped:
                failures.append(f"{relative}: container reference lacks sha256 digest: {stripped}")

    compose_ci = read("compose.ci.yaml")
    for service in ("postgres:", "minio:", "api:", "web:"):
        require(compose_ci, service, "compose.ci.yaml", failures)
    require(compose_ci, "ports: !reset []", "compose.ci.yaml", failures)

    if failures:
        print("SDLC delivery policy validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"SDLC delivery policy validation passed ({len(review_skills)} review skills).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
