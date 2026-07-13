from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from app.domain.document_intake import (
    DocumentProfileError,
    analyze_profile,
    cluster_fingerprint,
    evaluate_profile,
    exact_profile_match,
    ledger_expense_key,
    ledger_values_match,
    validate_fixture_suite,
)
from app.shared_contracts import (
    DocumentClusterProjectionContract,
    DocumentProfileVersionContract,
    ProfileEvaluationEvidenceContract,
)

CATALOG = Path(os.environ.get("FIXTURE_ROOT", "/app/fixtures")) / "document-intake-catalog.json"


def catalog():
    return json.loads(CATALOG.read_text())


def test_english_and_spanish_profiles_are_executable_shared_contracts():
    profiles = catalog()["profiles"]
    assert {item["profile"]["languageTag"] for item in profiles} == {"en", "es"}
    for item in profiles:
        profile = DocumentProfileVersionContract.model_validate(item["profile"])
        evidence = ProfileEvaluationEvidenceContract.model_validate(item["evaluationEvidence"])
        assert profile.content_hash and evidence.passed is True
        assert evidence.supported_field_exactness == 1
        assert evidence.source_location_exactness == 1
        assert evidence.unknown_safe_routing_rate == 1


def test_supported_fixtures_reproduce_fields_locations_and_fingerprints():
    for item in catalog()["profiles"]:
        profile = item["profile"]
        for fixture in item["fixtureSet"]["cases"]:
            if fixture["expectedOutcome"] != "recognized_profile_draft":
                continue
            first = analyze_profile(profile, fixture["ocrText"], fixture["mediaType"])
            second = analyze_profile(profile, fixture["ocrText"], fixture["mediaType"])
            assert first == second
            assert first.fingerprint in profile["acceptedFingerprints"]
            assert {field.name: field.value for field in first.fields} == fixture["expectedFields"]
            assert {field.name: field.source_location for field in first.fields} == fixture["expectedSourceLocations"]


def test_changed_and_unknown_layouts_never_exact_match_and_cluster_deterministically():
    data = catalog()
    profiles = [item["profile"] for item in data["profiles"]]
    fixtures = {
        fixture["id"]: fixture
        for item in data["profiles"]
        for fixture in item["fixtureSet"]["cases"]
    }
    for fixture_id in data["negativeFixtureIds"]:
        fixture = fixtures[fixture_id]
        assert exact_profile_match(profiles, fixture["ocrText"], fixture["mediaType"]) is None
        first = cluster_fingerprint(fixture["ocrText"], fixture["mediaType"])
        second = cluster_fingerprint(fixture["ocrText"], fixture["mediaType"])
        assert first == second
        projection = DocumentClusterProjectionContract(
            id=f"cluster-{fixture_id}",
            contract_id="contract-synthetic-agency-ngo-2026",
            fingerprint={
                "kind": "document_fingerprint",
                "id": f"fingerprint-{fixture_id}",
                "version": "document-layout-signals-v1",
                "sha256": first[1],
            },
            language_tag=first[0]["languageTag"],
            member_artifacts=[],
            status="suggested",
            canonical=False,
            projection_hash="1" * 64,
        )
        assert projection.canonical is False and projection.status == "suggested"


def test_shifted_layout_with_same_labels_and_values_cannot_reuse_an_accepted_fingerprint():
    item = catalog()["profiles"][0]
    profile = item["profile"]
    supported = next(
        fixture
        for fixture in item["fixtureSet"]["cases"]
        if fixture["caseKind"] == "supported_layout"
    )
    shifted = supported["ocrText"].replace(
        "Date:",
        "UNDECLARED LAYOUT ROW 1\nUNDECLARED LAYOUT ROW 2\nUNDECLARED LAYOUT ROW 3\nDate:",
    )
    original = analyze_profile(profile, supported["ocrText"], supported["mediaType"])
    changed = analyze_profile(profile, shifted, supported["mediaType"])
    assert original.fingerprint != changed.fingerprint
    assert changed.signals["pageGeometry"]["nonEmptyLineCount"] == (
        original.signals["pageGeometry"]["nonEmptyLineCount"] + 3
    )
    assert exact_profile_match([profile], shifted, supported["mediaType"]) is None


@pytest.mark.parametrize("fixture_selector", ["negative_only", "single_supported"])
def test_fixture_evaluation_rejects_vacuous_or_underrepresented_suites(fixture_selector):
    item = catalog()["profiles"][0]
    cases = item["fixtureSet"]["cases"]
    if fixture_selector == "negative_only":
        malformed = [case for case in cases if case["caseKind"] != "supported_layout"]
    else:
        malformed = [
            next(case for case in cases if case["caseKind"] == "supported_layout"),
            *[case for case in cases if case["caseKind"] != "supported_layout"],
        ]
    with pytest.raises(DocumentProfileError, match="two supported layouts"):
        validate_fixture_suite(item["profile"], malformed)


def test_declared_fingerprint_and_ledger_contracts_are_executable():
    profile = deepcopy(catalog()["profiles"][0]["profile"])
    profile["fingerprintSpecification"]["version"] = "undeclared-v9"
    with pytest.raises(DocumentProfileError, match="supported executable"):
        analyze_profile(profile, "Vendor: Synthetic Facilities Vendor A", "application/pdf")

    profile = deepcopy(catalog()["profiles"][0]["profile"])
    renamed = {
        "vendorName": "Synthetic Facilities Vendor A",
        "serviceDate": "2026-06-10",
        "claimAmount": "1850.00",
        "ledgerReference": "VENDOR-INVOICE-EXP-002",
    }
    profile["ledgerMatchRule"] = {
        "sourceReferenceField": "ledgerReference",
        "amountField": "claimAmount",
        "dateField": "serviceDate",
        "vendorField": "vendorName",
        "required": True,
    }
    profile["requiredFields"] = [
        {**field, "name": replacement}
        for field, replacement in zip(
            profile["requiredFields"],
            ("vendorName", "serviceDate", "claimAmount", "ledgerReference"),
            strict=True,
        )
    ]
    assert ledger_expense_key(profile, renamed) == "EXP-002"
    assert ledger_values_match(
        profile,
        renamed,
        expense_date="2026-06-10",
        vendor="Synthetic Facilities Vendor A",
        amount="1850.00",
    )


def test_catalog_evaluation_is_reproducible_from_exact_fixture_inputs():
    for item in catalog()["profiles"]:
        expected = item["evaluationEvidence"]
        actual = evaluate_profile(
            item["profile"],
            item["fixtureSet"]["cases"],
            ocr_version=expected["ocrVersion"],
        )
        assert actual["resultHash"] == expected["resultHash"]
        assert actual["results"] == expected["results"]
