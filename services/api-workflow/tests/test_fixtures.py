import csv
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path

fixture_root = os.environ.get("FIXTURE_ROOT")
FIXTURES = Path(fixture_root) if fixture_root else Path(__file__).resolve().parents[3] / "packages" / "test-fixtures"

def test_scenario_is_synthetic_and_complete() -> None:
    scenario = json.loads((FIXTURES / "scenario.json").read_text())
    assert scenario["syntheticOnly"] is True
    assert len(scenario["personas"]) == 5
    assert {item["role"] for item in scenario["personas"]} == {
        "configuration_administrator", "ngo_preparer", "ngo_approver", "government_reviewer", "auditor"
    }
    assert {(item["userId"], item["role"]) for item in scenario["accessAssignments"]} == {
        ("user-config-admin", "configuration_administrator"),
        ("user-auditor", "auditor"),
    }
    assert scenario["initialConfiguration"]["status"] == "draft"
    assert scenario["expected"]["finalState"] == "government_approved"

def test_ledger_totals_match_machine_readable_expectations() -> None:
    expected = json.loads((FIXTURES / "expected.json").read_text())
    with (FIXTURES / "files" / "ledger-june-2026.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == expected["ledgerRowCount"]
    assert sum(Decimal(row["amount"]) for row in rows) == Decimal(expected["ledgerTotal"])
    category_totals: dict[str, Decimal] = {}
    for row in rows:
        category_totals[row["budget_category"]] = category_totals.get(row["budget_category"], Decimal("0")) + Decimal(row["amount"])
    assert {key: str(value) for key, value in category_totals.items()} == expected["categoryTotals"]

def test_fixture_hash_manifest_matches_bytes() -> None:
    hashes = json.loads((FIXTURES / "fixture-hashes.json").read_text())
    for filename, expected_hash in hashes.items():
        actual = hashlib.sha256((FIXTURES / "files" / filename).read_bytes()).hexdigest()
        assert actual == expected_hash, filename

def test_fixture_text_is_non_branded_and_contains_no_real_personal_data() -> None:
    forbidden = ("shoken", "passport", "social security", "routing number", "date of birth")
    text_sources = [FIXTURES / "scenario.json", FIXTURES / "expected.json", FIXTURES / "files" / "ledger-june-2026.csv"]
    combined = "\n".join(path.read_text().lower() for path in text_sources)
    assert not any(term in combined for term in forbidden)
