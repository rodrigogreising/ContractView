from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "check_recovery_certification.py"
SPEC = importlib.util.spec_from_file_location("check_recovery_certification", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
RECORD = json.loads(MODULE.DEFAULT_RECORD.read_text(encoding="utf-8"))


class RecoveryCertificationTests(unittest.TestCase):
    def validate(self, record: dict[str, object] | None = None, merged: bool = True) -> list[str]:
        return MODULE.validate_record(record or copy.deepcopy(RECORD), ROOT, lambda _sha: merged)

    def test_current_record_passes(self) -> None:
        self.assertEqual([], self.validate())

    def test_missing_done_issue_fails(self) -> None:
        record = copy.deepcopy(RECORD)
        record["historicalDoneAudit"].pop()  # type: ignore[index]
        self.assertTrue(any("exactly the 37" in value for value in self.validate(record)))

    def test_legacy_approval_must_be_invalidated(self) -> None:
        record = copy.deepcopy(RECORD)
        legacy = record["historicalDoneAudit"][0]  # type: ignore[index]
        legacy["approvalDisposition"] = "retained"
        self.assertTrue(any("provisional legacy approval" in value for value in self.validate(record)))

    def test_legacy_issue_requires_superseding_recovery(self) -> None:
        record = copy.deepcopy(RECORD)
        legacy = record["historicalDoneAudit"][0]  # type: ignore[index]
        legacy["supersededBy"] = []
        self.assertTrue(any("superseding recovery" in value for value in self.validate(record)))

    def test_stale_recovery_merge_fails(self) -> None:
        self.assertTrue(any("not in origin/master" in value for value in self.validate(merged=False)))

    def test_exception_requires_owner_and_control(self) -> None:
        record = copy.deepcopy(RECORD)
        del record["exceptions"][0]["owner"]  # type: ignore[index]
        self.assertTrue(any("every exception" in value for value in self.validate(record)))

    def test_continuation_cannot_be_prematurely_unblocked(self) -> None:
        record = copy.deepcopy(RECORD)
        record["continuationGate"]["state"] = "unblocked"  # type: ignore[index]
        self.assertTrue(any("cannot be unblocked" in value for value in self.validate(record)))

    def test_decision_must_retain_exceptions(self) -> None:
        record = copy.deepcopy(RECORD)
        record["decision"] = "Certified"
        self.assertTrue(any("Certified with exceptions" in value for value in self.validate(record)))


if __name__ == "__main__":
    unittest.main()
