import json
import os
from pathlib import Path

from app.domain.document_intake import (
    analyze_profile,
    cluster_fingerprint,
    evaluate_profile,
    exact_profile_match,
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
