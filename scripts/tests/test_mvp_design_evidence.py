"""Executable positive contract for SUB-74's configurable intake design."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/architecture/document-intake-mvp-policy.json"
COVERAGE = ROOT / "docs/sdlc/issue-evidence-coverage.json"
PREREQUISITES = ROOT / "docs/sdlc/issue-prerequisites.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_scope_owners_lifecycle_and_ontology_are_explicit() -> None:
    policy = load_json(POLICY)

    assert policy["controllingIssue"] == "SUB-74"
    assert policy["epic"] == "SUB-73"
    assert policy["deploymentModel"] == "modular-monolith"
    assert policy["implementationStories"] == ["SUB-75", "SUB-76", "SUB-77", "SUB-78"]
    assert policy["profileLifecycle"] == [
        "draft",
        "tested",
        "approved",
        "active",
        "superseded",
        "retired",
    ]
    assert set(policy["owners"]) == {
        "configuration",
        "artifacts",
        "extraction",
        "provenance",
        "web",
    }
    assert policy["profileContract"]["ontologyComposition"] == [
        "Artifact",
        "Schema",
        "Field",
        "Mapping",
        "Rule",
        "Workflow",
        "View",
        "ConfigurationBundle",
        "Event",
    ]
    assert policy["profileContract"]["activeBundleReference"] == (
        "exact_profile_id_and_version"
    )
    assert policy["profileContract"]["activationIsProspective"] is True
    assert policy["profileContract"]["historicalReferencesAreImmutable"] is True
    assert policy["canonicalInvariants"] == {
        "submittedDataImmutable": True,
        "stakeholderSpecificCopiesAllowed": False,
        "profileActivationRequiresApprovedState": True,
        "unapprovedConfigurationRuntimeUseAllowed": False,
    }


def test_cluster_contract_is_deterministic_noncanonical_and_non_authoritative() -> None:
    cluster = load_json(POLICY)["clusterProjection"]

    assert cluster["canonical"] is False
    assert cluster["deterministic"] is True
    assert cluster["fingerprintAlgorithm"] == "sha256-canonical-json-v1"
    assert cluster["suggestionCreatesProfileAssignment"] is False
    assert cluster["administratorConfirmationRequired"] is True
    assert set(cluster["signals"]) == {
        "artifact_media_type",
        "language_tag",
        "normalized_text_tokens",
        "page_geometry",
        "anchor_positions",
    }


def test_supported_and_unknown_routing_have_positive_acceptance_contracts() -> None:
    policy = load_json(POLICY)
    routing = policy["extractionRouting"]
    evaluation = policy["fixtureEvaluation"]

    assert routing == {
        "supportedMatchResult": "recognized_profile_draft",
        "unknownLayoutResult": "needs_profile_review",
        "changedLayoutResult": "needs_profile_review",
        "canonicalExpenseCreatedForUnknown": False,
        "validationRunCreatedForUnknown": False,
        "humanReviewRequiredBeforeCanonicalUse": True,
    }
    profiles = {
        (profile["artifactClass"], profile["languageTag"]): profile["fixtureCountMinimum"]
        for profile in policy["supportedSyntheticProfiles"]
    }
    assert profiles == {("vendor_invoice", "en"): 2, ("vendor_invoice", "es"): 2}
    assert evaluation["dataSource"] == "closed_synthetic_catalogs_and_deterministic_generators"
    assert set(evaluation["requiredCases"]) == {
        "english_supported_layout",
        "spanish_supported_layout",
        "changed_layout",
        "unknown_layout",
        "profile_successor_historical_replay",
    }
    assert evaluation["supportedFieldExactness"] == 1.0
    assert evaluation["supportedSourceLocationExactness"] == 1.0
    assert evaluation["unknownSafeRoutingRate"] == 1.0
    assert evaluation["canonicalMutationOnUnknown"] == 0
    assert evaluation["identicalInputFingerprintEquality"] is True
    assert evaluation["historicalReferenceStability"] is True


def test_runtime_automation_and_human_authority_are_bounded() -> None:
    policy = load_json(POLICY)
    automation = policy["runtimeAutomation"]

    assert automation["localOcrAllowed"] is True
    assert automation["hostedModelAllowed"] is False
    assert automation["runtimeLlmAllowed"] is False
    assert automation["aiProfileDraftingAllowed"] is False
    assert automation["aiAuthorityAllowed"] is False
    assert automation["deterministicProfileMatchingRequired"] is True
    assert automation["deterministicNormalizationRequired"] is True
    assert policy["runtimeEvidence"] == {
        "requiredVersionReferences": [
            "artifact_hash",
            "ocr_version",
            "parser_version",
            "fingerprint_specification_version",
            "profile_id",
            "profile_version",
            "configuration_bundle_version",
            "human_review_event_id",
        ],
        "snapshotReferencesAreImmutable": True,
    }
    assert policy["authority"]["system"] == []
    assert policy["authority"]["ai"] == []
    assert set(policy["roleWorkspaceIntent"]) == {
        "configurationAdministrator",
        "ngoPreparer",
        "ngoApprover",
        "governmentReviewer",
        "auditor",
    }
    assert policy["authority"]["ngoApprover"] == ["attest", "submit"]
    assert policy["authority"]["governmentReviewer"] == ["return", "approve"]
    assert policy["authority"]["auditor"] == ["read_reconstruction"]
    assert policy["roleContextContract"] == {
        "requiredPresentation": [
            "identity",
            "organization",
            "role",
            "authorized_contract",
            "next_action",
            "bounded_authority",
            "unavailable_actions",
            "exact_configuration_profile_context",
            "logout",
        ],
        "activeContextIsProspective": True,
        "assignedWorkContextIsHistorical": True,
        "auditorActiveConfigurationVisible": False,
        "clientProjectionGrantsAuthority": False,
    }


def test_narrative_design_evidence_is_linked_and_traceable() -> None:
    documents = {
        "charter": ROOT / "docs/product/document-intake-mvp-charter.md",
        "adr": ROOT / "docs/adr/0003-configurable-document-intake-mvp.md",
        "boundaries": ROOT / "docs/architecture/service-boundaries.md",
        "journey": ROOT / "docs/journeys/12-configurable-document-intake-mvp.md",
        "security": ROOT / "docs/sdlc/poc-security-privacy.md",
        "ai": ROOT / "docs/sdlc/poc-ai-governance.md",
        "implementation": ROOT / "docs/sdlc/implementation/SUB-74-document-intake-design.md",
    }
    contents = {name: path.read_text(encoding="utf-8") for name, path in documents.items()}

    for content in contents.values():
        assert "SUB-74" in content
    assert "Journey 12" in contents["charter"]
    assert "DocumentProfileVersion" in contents["adr"]
    assert "needs_profile_review" in contents["boundaries"]
    assert "normal login/logout" in contents["journey"]
    assert "closed synthetic catalogs and deterministic generators" in contents["security"]
    assert "no runtime AI capability" in contents["ai"]
    assert "introduces no" in contents["implementation"]

    trace = (ROOT / "docs/sdlc/requirements-traceability.md").read_text(encoding="utf-8")
    assert "| Boundary evidence |" in trace
    assert "| Release evidence |" in trace
    trace_rows = [line for line in trace.splitlines() if line.startswith("| `MVP-REQ-")]
    assert len(trace_rows) == 10
    for index, row in enumerate(trace_rows, start=1):
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert len(columns) == 7
        assert f"MVP-REQ-{index:02d}" in columns[0]
        assert "docs/architecture/" in columns[3]
        assert "scripts/tests/" in columns[5] or "docs/journeys/" in columns[5]
    for story in ("SUB-75", "SUB-76", "SUB-77", "SUB-78"):
        assert story in trace


def test_sdlc_registries_declare_exact_reviews_labels_and_prerequisites() -> None:
    coverage = load_json(COVERAGE)["SUB-74"]
    prerequisites = load_json(PREREQUISITES)["SUB-74"]

    assert coverage["projectStatus"] == "Design Review"
    assert coverage["includeJourneyInCleanRuntime"] is False
    assert coverage["reviewSkills"] == [
        "cv-review-product-intake",
        "cv-review-requirements-traceability",
        "cv-review-adr-architecture",
        "cv-review-boundary-review",
        "cv-review-security-privacy",
        "cv-review-ai-governance",
        "cv-review-journey-certification",
        "cv-review-implementation-tests",
    ]
    expected_labels = {
        "gate:adr",
        "gate:architecture",
        "gate:security-privacy",
        "gate:config-governance",
        "risk:configuration-drift",
        "risk:sensitive-data",
    }
    assert set(coverage["riskAndGateLabels"]) == expected_labels
    assert set(coverage["riskCoverage"]) == expected_labels
    assert prerequisites == [
        {
            "issue": "SUB-17",
            "mergeSha": "382876b7746e1147ee112e23bc80b95b90114d3a",
            "postMergeVerified": True,
        },
        {
            "issue": "SUB-56",
            "mergeSha": "d8f99ebd27a5d3d99a6d1ad59477e94acd142ce3",
            "postMergeVerified": True,
        },
        {
            "issue": "SUB-80",
            "mergeSha": "0d41b540c47f116f6b25d88aea39138a4ca2f043",
            "postMergeVerified": True,
        },
    ]
