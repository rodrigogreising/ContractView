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
    assert {item["languageTag"] for item in scenario["documentIntake"]["profiles"]} == {"en", "es"}
    assert len(scenario["initialConfiguration"]["documentProfiles"]) == 2

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


def test_binary_fixture_metadata_and_text_match_the_closed_synthetic_catalog() -> None:
    scenario = json.loads((FIXTURES / "scenario.json").read_text())
    expected_vendors = {
        invoice["vendor"]
        for invoice in scenario["fixtureData"]["vendorInvoices"]
    }
    intake_by_filename = {
        item["filename"]: item
        for item in scenario["documentIntake"]["fixtures"]
    }
    expected_pdf_names = {
        f"vendor-invoice-{invoice['expense_id'].lower()}.pdf"
        for invoice in scenario["fixtureData"]["vendorInvoices"]
    } | set(intake_by_filename)
    assert {path.name for path in (FIXTURES / "files").glob("*.pdf")} == expected_pdf_names
    pdf_text = []
    for path in sorted((FIXTURES / "files").glob("*.pdf")):
        result = subprocess.run(
            ["pdftotext", str(path), "-"], check=True, capture_output=True, text=True
        )
        pdf_text.append(result.stdout)
        if path.name in intake_by_filename:
            expected = intake_by_filename[path.name]["ocrText"].splitlines()
            assert result.stdout.splitlines()[0].strip() == expected[0]
        else:
            assert result.stdout.splitlines()[0].strip() in expected_vendors
        metadata = subprocess.run(
            ["pdfinfo", str(path)], check=True, capture_output=True, text=True
        ).stdout
        assert re.search(r"^Title:\s+Synthetic (?:vendor invoice|document-intake fixture)$", metadata, re.M)
        assert "Author:          Synthetic Fixture Generator" in metadata
        assert "Creator:         Synthetic Fixture Generator" in metadata
        assert "Producer:        Synthetic Fixture Generator" in metadata
    combined_pdf_text = "\n".join(pdf_text)
    assert expected_vendors <= {
        line.strip()
        for line in combined_pdf_text.splitlines()
        if line.strip().startswith("Synthetic ")
    }


def test_document_intake_catalog_has_exact_profile_and_evaluation_evidence() -> None:
    catalog = json.loads((FIXTURES / "document-intake-catalog.json").read_text())
    scenario = json.loads((FIXTURES / "scenario.json").read_text())
    assert catalog["catalogVersion"] == scenario["documentIntake"]["catalogVersion"]
    assert {item["profile"]["languageTag"] for item in catalog["profiles"]} == {"en", "es"}
    assert catalog["negativeFixtureIds"] == ["profile-changed-layout", "profile-unknown-layout"]
    for item in catalog["profiles"]:
        kinds = [case["caseKind"] for case in item["fixtureSet"]["cases"]]
        assert kinds.count("supported_layout") >= 2
        assert "changed_layout" in kinds and "unknown_layout" in kinds
        evidence = item["evaluationEvidence"]
        assert evidence["passed"] is True
        assert evidence["supportedFieldExactness"] == 1.0
        assert evidence["sourceLocationExactness"] == 1.0
        assert evidence["unknownSafeRoutingRate"] == 1.0
        assert len(evidence["resultHash"]) == 64
        assert all(result["passed"] for result in evidence["results"])

    for path in sorted((FIXTURES / "files").glob("*.xlsx")):
        with zipfile.ZipFile(path) as archive:
            metadata = "\n".join(
                archive.read(name).decode("utf-8")
                for name in archive.namelist()
                if name.startswith("docProps/")
            )
        assert "Synthetic Fixture Generator" in metadata
        assert re.search(r"<dc:creator>Synthetic Fixture Generator</dc:creator>", metadata)
