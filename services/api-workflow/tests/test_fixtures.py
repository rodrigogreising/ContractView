import csv
import hashlib
import json
import os
from decimal import Decimal
from email.utils import parseaddr
from pathlib import Path
import re
import subprocess
import zipfile

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

def test_fixture_identities_match_the_closed_synthetic_catalog() -> None:
    scenario = json.loads((FIXTURES / "scenario.json").read_text())
    assert {item["name"] for item in scenario["organizations"]} == {
        "Synthetic Public Agency",
        "Synthetic Community Nonprofit",
        "Synthetic Oversight Unit",
        "Synthetic Platform Operations",
    }
    assert {item["displayName"] for item in scenario["personas"]} == {
        "Synthetic Configuration Administrator",
        "Synthetic NGO Preparer",
        "Synthetic NGO Approver",
        "Synthetic Government Reviewer",
        "Synthetic Auditor",
    }
    for persona in scenario["personas"]:
        address = parseaddr(persona["email"])[1]
        assert address == persona["email"]
        assert address.endswith("@example.test")
    allowed_vendors = {
        "Synthetic Community Nonprofit",
        "Synthetic Facilities Vendor A",
        "Synthetic Program Supplies Vendor B",
        "Synthetic Equipment Vendor C",
    }
    rows = scenario["fixtureData"]["ledgerRows"]
    assert {row["vendor"] for row in rows} == allowed_vendors
    assert all(row["vendor"].startswith("Synthetic ") for row in rows)
    assert all(
        row["employee_reference"].startswith("SYNTHETIC-EMPLOYEE-")
        for row in scenario["fixtureData"]["payrollRows"]
    )


def test_binary_fixture_metadata_and_text_are_explicitly_synthetic() -> None:
    expected_vendors = {
        invoice["vendor"]
        for invoice in json.loads((FIXTURES / "scenario.json").read_text())["fixtureData"]["vendorInvoices"]
    }
    pdf_text = []
    for path in sorted((FIXTURES / "files").glob("*.pdf")):
        result = subprocess.run(
            ["pdftotext", str(path), "-"], check=True, capture_output=True, text=True
        )
        pdf_text.append(result.stdout)
        assert "Test fixture only" in result.stdout
        assert "no real organization" in result.stdout.lower()
    combined_pdf_text = "\n".join(pdf_text)
    assert expected_vendors <= {
        line.strip()
        for line in combined_pdf_text.splitlines()
        if line.strip().startswith("Synthetic ")
    }

    for path in sorted((FIXTURES / "files").glob("*.xlsx")):
        with zipfile.ZipFile(path) as archive:
            metadata = "\n".join(
                archive.read(name).decode("utf-8")
                for name in archive.namelist()
                if name.startswith("docProps/")
            )
        assert "Synthetic Fixture Generator" in metadata
        assert re.search(r"<dc:creator>Synthetic Fixture Generator</dc:creator>", metadata)
