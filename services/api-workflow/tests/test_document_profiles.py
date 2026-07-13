from copy import deepcopy
import json
from pathlib import Path

import psycopg
import pytest

from app.authorization import Actor, ForbiddenError, Role
from app.configuration import active_summary
from app.configuration import (
    approve_version,
    configuration_version_detail,
    get_draft_details,
    rollback_version,
    supersede_version,
    test_draft as certify_configuration_draft,
    update_draft,
)
from app.document_profiles import (
    InvalidDocumentProfile,
    activate_profile_references_tx,
    approve_profile,
    create_profile_draft,
    list_profiles,
    profile_detail,
    test_profile as evaluate_profile_version,
)
from app.runtime import database
from app.application.ports.statements import Statement
from app.application.transaction import transaction as application_database
from configuration_helpers import ensure_active_configuration

CONTRACT = "contract-synthetic-agency-ngo-2026"
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
CATALOG = Path("/app/fixtures/document-intake-catalog.json")


def profile_state_fingerprint() -> tuple:
    tables = (
        "document_profile_versions",
        "document_profile_fixture_sets",
        "document_profile_evaluations",
        "document_profile_approvals",
        "document_profile_lifecycle_events",
        "document_profile_active_assignments",
        "document_profile_cluster_associations",
    )
    with database() as connection:
        return tuple(
            (
                table,
                *connection.execute(
                    f"""select count(*),md5(coalesce(string_agg(to_jsonb(t)::text,'|'
                         order by to_jsonb(t)::text),'')) from {table} t"""
                ).fetchone(),
            )
            for table in tables
        )


def test_seeded_profiles_have_exact_immutable_fixture_and_evaluation_evidence():
    profiles = list_profiles(ADMIN, CONTRACT)
    baseline = {
        item["profile"]["profileKey"]: item["state"]
        for item in profiles if item["profile"]["version"] == 1
    }
    assert baseline.keys() >= {"vendor_invoice_en", "vendor_invoice_es"}
    assert set(baseline.values()) <= {"approved", "active"}
    for item in profiles:
        if item["profile"]["version"] != 1:
            continue
        assert item["evaluationEvidence"]["passed"] is True
        assert item["evaluationEvidence"]["supportedFieldExactness"] == 1.0
        assert item["evaluationEvidence"]["sourceLocationExactness"] == 1.0
        assert item["evaluationEvidence"]["unknownSafeRoutingRate"] == 1.0
        assert item["approval"]["approvedRole"] == "configuration_administrator"
        assert item["profile"]["fixtureSet"]["sha256"] == item["fixtureSet"]["contentHash"]


def test_wrong_role_profile_create_is_denied_before_mutation():
    item = json.loads(CATALOG.read_text())["profiles"][0]
    definition = deepcopy(item["profile"])
    before = profile_state_fingerprint()
    with pytest.raises(ForbiddenError):
        create_profile_draft(
            PREPARER,
            CONTRACT,
            definition,
            item["fixtureSet"]["cases"],
            "Unauthorized profile creation",
        )
    assert profile_state_fingerprint() == before


def test_successor_profile_requires_test_and_human_approval_before_prospective_activation():
    data = json.loads(CATALOG.read_text())
    english = data["profiles"][0]
    definition = deepcopy(english["profile"])
    for field in (
        "id", "contractId", "version", "lifecycle", "acceptedFingerprints",
        "fixtureSet", "evaluationEvidence", "predecessor", "successor", "contentHash",
    ):
        definition.pop(field, None)
    definition["predecessorVersionId"] = english["profile"]["id"]
    created = create_profile_draft(
        ADMIN,
        CONTRACT,
        definition,
        english["fixtureSet"]["cases"],
        "Create deterministic English successor",
    )
    successor_id = created["profile"]["id"]
    assert created["state"] == "draft"
    with pytest.raises(InvalidDocumentProfile, match="tested profile"):
        approve_profile(ADMIN, successor_id, "Cannot approve an untested profile")
    tested = evaluate_profile_version(
        ADMIN, successor_id, "Evaluate exact supported and negative fixtures"
    )
    assert tested["state"] == "tested"
    assert tested["evaluationEvidence"]["passed"] is True
    approved = approve_profile(ADMIN, successor_id, "Human approval of exact evidence")
    assert approved["state"] == "approved"

    active = ensure_active_configuration(ADMIN, CONTRACT)
    spanish = next(
        item for item in list_profiles(ADMIN, CONTRACT)
        if item["profile"]["profileKey"] == "vendor_invoice_es" and item["profile"]["version"] == 1
    )
    references = [
        {
            "kind": "document_profile",
            "id": successor_id,
            "version": approved["profile"]["version"],
            "sha256": approved["profile"]["contentHash"],
        },
        {
            "kind": "document_profile",
            "id": spanish["profile"]["id"],
            "version": spanish["profile"]["version"],
            "sha256": spanish["profile"]["contentHash"],
        },
    ]
    with application_database() as connection:
        activate_profile_references_tx(
            connection,
            ADMIN,
            CONTRACT,
            active["id"],
            references,
            "Prospective activation proof rolled back after assertion",
        )
        row = connection.configuration.execute(
            Statement.DOCUMENT_PROFILES_READ_DOCUMENT_PROFILE_ACTIVE_ASSIGNMENTS_009,
            (CONTRACT, "vendor_invoice_en"),
        ).fetchone()
        assert row[0] == successor_id
        # Deliberately omit commit: the application transaction rolls this proof back.
    assert profile_detail(ADMIN, successor_id)["state"] == "approved"
    assert active_summary(ADMIN, CONTRACT)["id"] == active["id"]

    with database() as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
            connection.execute(
                "update document_profile_versions set payload='{}' where id=%s",
                (successor_id,),
            )


def test_configuration_rollback_reactivates_exact_historical_profile_with_new_event():
    baseline_configuration = ensure_active_configuration(ADMIN, CONTRACT)
    profiles = list_profiles(ADMIN, CONTRACT)
    english_v1 = next(
        item for item in profiles
        if item["profile"]["profileKey"] == "vendor_invoice_en"
        and item["profile"]["version"] == 1
    )
    english_v2 = next(
        item for item in profiles
        if item["profile"]["profileKey"] == "vendor_invoice_en"
        and item["profile"]["version"] == 2
    )
    spanish_v1 = next(
        item for item in profiles
        if item["profile"]["profileKey"] == "vendor_invoice_es"
        and item["profile"]["version"] == 1
    )
    baseline_payload = configuration_version_detail(
        ADMIN, baseline_configuration["id"]
    )["configuration"]
    successor_payload = deepcopy(baseline_payload)
    successor_payload["documentProfiles"] = [
        {
            "kind": "document_profile",
            "id": english_v2["profile"]["id"],
            "version": english_v2["profile"]["version"],
            "sha256": english_v2["profile"]["contentHash"],
        },
        {
            "kind": "document_profile",
            "id": spanish_v1["profile"]["id"],
            "version": spanish_v1["profile"]["version"],
            "sha256": spanish_v1["profile"]["contentHash"],
        },
    ]
    draft = get_draft_details(ADMIN, CONTRACT)
    revised = update_draft(
        ADMIN, CONTRACT, successor_payload, expected_revision=draft["revision"]
    )
    tested = certify_configuration_draft(
        ADMIN,
        CONTRACT,
        "Evaluate configuration with English profile successor",
        expected_revision=revised["revision"],
    )
    approve_version(ADMIN, tested["id"], "Approve profile successor configuration")
    supersede_version(
        ADMIN,
        baseline_configuration["id"],
        tested["id"],
        "Activate English profile successor prospectively",
    )

    rollback = rollback_version(
        ADMIN,
        CONTRACT,
        baseline_configuration["id"],
        "Prepare exact historical profile rollback",
    )
    approve_version(ADMIN, rollback["id"], "Approve exact historical profile rollback")
    supersede_version(
        ADMIN,
        tested["id"],
        rollback["id"],
        "Activate exact historical profile rollback prospectively",
    )

    with database() as connection:
        active_profile = connection.execute(
            """select profile_version_id from document_profile_active_assignments
                where contract_id=%s and profile_key='vendor_invoice_en'""",
            (CONTRACT,),
        ).fetchone()
        rollback_event = connection.execute(
            """select action,configuration_version_id,event_hash
                 from document_profile_lifecycle_events
                where profile_version_id=%s and action='rollback'
                order by sequence desc limit 1""",
            (english_v1["profile"]["id"],),
        ).fetchone()
        domain_event = connection.execute(
            """select event_type from domain_events
                where aggregate_id=%s and payload->>'action'='rollback'
                order by occurred_at desc limit 1""",
            (english_v1["profile"]["id"],),
        ).fetchone()
    assert active_profile == (english_v1["profile"]["id"],)
    assert rollback_event[0:2] == ("rollback", rollback["id"])
    assert len(rollback_event[2]) == 64
    assert domain_event == ("profile_rollback_activated",)
