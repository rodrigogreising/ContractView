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
        "issue": "SUB-69",
        "projectStatus": "Design Review",
        "branch": "codex/sub-69-policy",
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
        "checks": [
            {
                "command": "python -m unittest",
                "exitCode": 0,
                "result": "passed",
                "recordedAt": "2026-07-11T12:00:00Z",
                "testCount": 8,
            }
        ],
        "certification": {
            "behaviorChanged": False,
            "rationale": "Process-only change is certified by policy and validator tests.",
            "requiredReviewSkills": ["cv-review-implementation-tests"],
            "evidenceKinds": ["policy", "unit"],
            "riskCoverage": {},
            "cleanRuntimeRequired": False,
        },
        "review": {
            "decision": "Pending",
            "reviewer": "Codex AI",
            "method": "ai",
            "reviewSkills": ["cv-review-implementation-tests"],
            "reviewedBaseSha": SHA_A,
            "reviewedHeadSha": SHA_B,
            "evidenceAdequate": False,
            "findings": [],
        },
        "humanApprovalRequirement": {
            "required": False,
            "basis": "No governance or real-world authority decision is in scope.",
        },
    }


def state(**changes: object) -> object:
    values = {
        "branch": "codex/sub-69-policy",
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

    def test_risk_label_without_evidence_coverage_fails(self) -> None:
        evidence = manifest()
        evidence["riskAndGateLabels"] = ["gate:release-certification"]
        failures = self.validate(evidence)
        self.assertTrue(any("lack executable evidence coverage" in failure for failure in failures))

    def test_high_risk_ai_review_does_not_require_human_code_review(self) -> None:
        evidence = manifest()
        evidence["riskAndGateLabels"] = ["gate:release-certification"]
        evidence["certification"]["riskCoverage"] = {  # type: ignore[index]
            "gate:release-certification": ["Policy and negative validator tests"]
        }
        self.assertEqual([], self.validate(evidence))

    def test_behavior_change_requires_behavioral_evidence(self) -> None:
        evidence = manifest()
        evidence["certification"]["behaviorChanged"] = True  # type: ignore[index]
        failures = self.validate(evidence)
        self.assertTrue(any("evidence beyond policy or unit" in failure for failure in failures))

    def test_test_evidence_requires_exact_count(self) -> None:
        evidence = manifest()
        del evidence["checks"][0]["testCount"]  # type: ignore[index]
        failures = self.validate(evidence)
        self.assertTrue(any("exact testCount" in failure for failure in failures))

    def test_artifact_evidence_requires_hashes(self) -> None:
        evidence = manifest()
        evidence["certification"]["evidenceKinds"] = ["policy", "artifact"]  # type: ignore[index]
        failures = self.validate(evidence)
        self.assertTrue(any("artifact hashes" in failure for failure in failures))

    def test_explicit_human_authority_requirement_must_be_satisfied(self) -> None:
        evidence = manifest()
        evidence["humanApprovalRequirement"] = {
            "required": True,
            "basis": "Release owner signoff explicitly required",
        }
        failures = self.validate(evidence)
        self.assertTrue(any("human authority approval" in failure for failure in failures))

    def test_approved_ai_review_requires_adequate_evidence(self) -> None:
        evidence = manifest()
        evidence["review"]["decision"] = "Approved"  # type: ignore[index]
        failures = self.validate(evidence)
        self.assertTrue(any("adequate executable evidence" in failure for failure in failures))

    def test_completed_review_must_cover_every_required_ai_skill(self) -> None:
        evidence = manifest()
        evidence["certification"]["requiredReviewSkills"] = [  # type: ignore[index]
            "cv-review-implementation-tests",
            "cv-review-release-readiness",
        ]
        failures = self.validate(evidence)
        self.assertTrue(any("omits required AI reviews" in failure for failure in failures))

    def test_done_without_post_merge_verification_fails(self) -> None:
        evidence = copy.deepcopy(manifest())
        evidence["review"]["decision"] = "Approved"  # type: ignore[index]
        evidence["review"]["evidenceAdequate"] = True  # type: ignore[index]
        failures = self.validate(evidence, phase="done")
        self.assertTrue(any("completion evidence" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
