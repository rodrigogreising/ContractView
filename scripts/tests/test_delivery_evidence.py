from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_delivery_evidence.py"
SPEC = importlib.util.spec_from_file_location("validate_delivery_evidence", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


def manifest() -> dict[str, object]:
    return {
        "issue": "SUB-58",
        "projectStatus": "Design Review",
        "branch": "codex/sub-58-policy",
        "baseSha": SHA_A,
        "headSha": SHA_B,
        "pullRequestUrl": "https://github.com/example/repo/pull/2",
        "declaredScope": ["docs/", "scripts/"],
        "recordedAt": "2026-07-11T12:00:00Z",
        "prerequisites": [
            {"issue": "SUB-57", "mergeSha": SHA_C, "postMergeVerified": True}
        ],
        "riskAndGateLabels": [],
        "environment": {"python": "3.13"},
        "checks": [{"command": "test", "exitCode": 0, "result": "passed"}],
        "review": {
            "decision": "Pending",
            "reviewer": "Codex",
            "reviewedBaseSha": SHA_A,
            "reviewedHeadSha": SHA_B,
            "findings": [],
            "freshContextOrHuman": False,
        },
    }


def state(**changes: object) -> object:
    values = {
        "branch": "codex/sub-58-policy",
        "head_sha": SHA_B,
        "tracked_worktree_clean": True,
        "changed_files": ("docs/policy.md", "scripts/check.py"),
    }
    values.update(changes)
    return MODULE.RepositoryState(**values)


class DeliveryEvidenceTests(unittest.TestCase):
    def validate(
        self,
        evidence: dict[str, object] | None = None,
        *,
        phase: str = "review",
        repository_state: object | None = None,
        merged: bool = True,
    ) -> list[str]:
        return MODULE.validate_manifest(
            evidence or manifest(),
            phase,
            repository_state or state(),
            lambda _sha: merged,
        )

    def test_valid_review_evidence_passes(self) -> None:
        self.assertEqual([], self.validate())

    def test_direct_work_on_master_fails(self) -> None:
        evidence = manifest()
        evidence["branch"] = "master"
        failures = self.validate(evidence, repository_state=state(branch="master"))
        self.assertTrue(any("default branch" in failure for failure in failures))

    def test_mixed_issue_scope_fails(self) -> None:
        failures = self.validate(
            repository_state=state(changed_files=("docs/policy.md", "apps/web/app.tsx"))
        )
        self.assertTrue(any("mixed or undeclared" in failure for failure in failures))

    def test_missing_manifest_fields_fail(self) -> None:
        evidence = manifest()
        del evidence["checks"]
        self.assertTrue(any("missing required" in failure for failure in self.validate(evidence)))

    def test_stale_prerequisite_proof_fails(self) -> None:
        evidence = manifest()
        evidence["prerequisites"][0]["postMergeVerified"] = False  # type: ignore[index]
        failures = self.validate(evidence, merged=False)
        self.assertTrue(any("stale prerequisite" in failure for failure in failures))

    def test_review_time_mutation_fails(self) -> None:
        failures = self.validate(
            repository_state=state(head_sha=SHA_C, tracked_worktree_clean=False)
        )
        self.assertEqual(2, sum("review-time mutation" in failure for failure in failures))

    def test_high_risk_change_without_fresh_or_human_review_fails(self) -> None:
        evidence = manifest()
        evidence["riskAndGateLabels"] = ["gate:release-certification"]
        failures = self.validate(evidence)
        self.assertTrue(any("high-risk gates" in failure for failure in failures))

    def test_done_without_post_merge_verification_fails(self) -> None:
        evidence = copy.deepcopy(manifest())
        evidence["review"]["decision"] = "Approved"  # type: ignore[index]
        failures = self.validate(evidence, phase="done")
        self.assertTrue(any("completion evidence" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
