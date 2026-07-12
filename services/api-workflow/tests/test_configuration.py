import json
from hashlib import sha256
from pathlib import Path
import uuid

import psycopg
import pytest

from app.authorization import Actor, ForbiddenError, Role
from app.configuration import (
    InvalidConfiguration,
    activate_draft,
    activate_version,
    active_summary,
    approve_version,
    get_draft,
    lifecycle_history,
    retire_version,
    rollback_version,
    supersede_version,
    test_draft as certify_draft,
    update_draft,
)
from app.runtime import database

FIXTURE = Path("/app/fixtures/scenario.json")
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
GOVERNMENT = Actor("user-government-reviewer", "org-government", Role.GOVERNMENT_REVIEWER)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
CONTRACT = "contract-synthetic-agency-ngo-2026"


def draft_payload():
    return json.loads(FIXTURE.read_text())["initialConfiguration"]


def governance_fingerprint() -> tuple:
    tables = (
        "configuration_drafts",
        "configuration_versions",
        "configuration_test_evidence",
        "configuration_approvals",
        "configuration_lifecycle_events",
        "configuration_active_versions",
        "domain_events",
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


def test_direct_draft_to_active_is_rejected_without_mutation():
    update_draft(ADMIN, CONTRACT, draft_payload())
    before = governance_fingerprint()
    with pytest.raises(InvalidConfiguration, match="Direct draft-to-active"):
        activate_draft(ADMIN, CONTRACT)
    assert governance_fingerprint() == before
    assert active_summary(ADMIN, CONTRACT) is None


def test_complete_lifecycle_preserves_evidence_history_and_prospective_activation():
    first_payload = draft_payload()
    first_payload["package"]["label"] = "First governed package"
    update_draft(ADMIN, CONTRACT, first_payload)
    tested_one = certify_draft(ADMIN, CONTRACT, "Fixture suite passed for version one")
    assert tested_one["state"] == "tested"
    assert tested_one["version"] == 1
    assert len(tested_one["testEvidence"]["payloadHash"]) == 64
    assert len(tested_one["testEvidence"]["resultHash"]) == 64
    approved_one = approve_version(ADMIN, tested_one["id"], "Human approval for initial use")
    assert approved_one["state"] == "approved" and approved_one["approvalId"]
    active_one = activate_version(ADMIN, tested_one["id"], "Prospective initial activation")
    assert active_one["state"] == "active"

    second_payload = draft_payload()
    second_payload["package"]["label"] = "Second governed package"
    update_draft(ADMIN, CONTRACT, second_payload)
    tested_two = certify_draft(ADMIN, CONTRACT, "Fixture suite passed for version two")
    approve_version(ADMIN, tested_two["id"], "Human approval for successor")
    with pytest.raises(InvalidConfiguration, match="Supersede"):
        activate_version(ADMIN, tested_two["id"], "Invalid parallel activation")
    assert active_summary(ADMIN, CONTRACT)["id"] == tested_one["id"]
    supersede_version(
        ADMIN,
        tested_one["id"],
        tested_two["id"],
        "Replace version one prospectively",
    )
    assert active_summary(ADMIN, CONTRACT)["id"] == tested_two["id"]
    retire_version(ADMIN, tested_one["id"], "Retire superseded version one")

    rollback = rollback_version(
        ADMIN,
        CONTRACT,
        tested_one["id"],
        "Prepare governed rollback to version one definition",
    )
    assert rollback["state"] == "tested"
    assert rollback["rollbackTargetId"] == tested_one["id"]
    assert rollback["testEvidence"]["payloadHash"] == tested_one["testEvidence"]["payloadHash"]
    assert rollback["testEvidence"]["resultHash"] == tested_one["testEvidence"]["resultHash"]
    approve_version(ADMIN, rollback["id"], "Human approval for rollback candidate")
    supersede_version(
        ADMIN,
        tested_two["id"],
        rollback["id"],
        "Activate tested and approved rollback prospectively",
    )

    history = lifecycle_history(ADMIN, CONTRACT)["versions"]
    by_id = {item["id"]: item for item in history}
    assert by_id[tested_one["id"]]["state"] == "retired"
    assert by_id[tested_two["id"]]["state"] == "superseded"
    assert by_id[rollback["id"]]["state"] == "active"
    assert by_id[rollback["id"]]["active"] is True
    assert [event["state"] for event in by_id[tested_one["id"]]["history"]] == [
        "tested",
        "approved",
        "active",
        "superseded",
        "retired",
    ]
    assert by_id[rollback["id"]]["history"][0]["rollbackTargetVersionId"] == tested_one["id"]

    with database() as connection:
        stored = connection.execute(
            "select version,payload->'package'->>'label' from configuration_versions where contract_id=%s order by version",
            (CONTRACT,),
        ).fetchall()
        approval = connection.execute(
            "select approved_by,approved_role,rationale,approval_hash from configuration_approvals where configuration_version_id=%s",
            (tested_one["id"],),
        ).fetchone()
        test_evidence = connection.execute(
            "select payload_hash,results,result_hash from configuration_test_evidence where configuration_version_id=%s",
            (tested_one["id"],),
        ).fetchone()
    assert stored == [
        (1, "First governed package"),
        (2, "Second governed package"),
        (3, "First governed package"),
    ]
    assert approval[:3] == (
        ADMIN.user_id,
        ADMIN.role.value,
        "Human approval for initial use",
    )
    assert len(approval[3]) == 64
    expected_result_hash = sha256(
        json.dumps(
            {"payloadHash": test_evidence[0], "report": test_evidence[1]},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert test_evidence[2] == expected_result_hash

    for table in (
        "configuration_versions",
        "configuration_test_evidence",
        "configuration_approvals",
        "configuration_lifecycle_events",
    ):
        with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
            with database() as connection:
                connection.execute(f"delete from {table}")

    with pytest.raises(psycopg.errors.UniqueViolation):
        with database() as connection:
            connection.execute(
                """insert into configuration_lifecycle_events
                   (id,configuration_version_id,contract_id,state,action,
                    actor_id,actor_role,actor_organization_id,rationale,
                    test_evidence_id,approval_id,predecessor_version_id,
                    successor_version_id,rollback_target_version_id,event_hash)
                   select %s,configuration_version_id,contract_id,state,action,
                          actor_id,actor_role,actor_organization_id,rationale,
                          test_evidence_id,approval_id,predecessor_version_id,
                          successor_version_id,rollback_target_version_id,%s
                   from configuration_lifecycle_events
                   where configuration_version_id=%s and state='retired'""",
                (
                    f"duplicate-lifecycle-{uuid.uuid4().hex}",
                    "0" * 64,
                    tested_one["id"],
                ),
            )


def test_invalid_and_out_of_order_transitions_are_rejected():
    active = active_summary(ADMIN, CONTRACT)
    with pytest.raises(InvalidConfiguration, match="superseded"):
        retire_version(ADMIN, active["id"], "Cannot retire active")
    with pytest.raises(InvalidConfiguration, match="superseded or retired"):
        rollback_version(ADMIN, CONTRACT, active["id"], "Cannot roll back active")

    update_draft(ADMIN, CONTRACT, draft_payload())
    tested = certify_draft(ADMIN, CONTRACT, "Test candidate for invalid ordering")
    with pytest.raises(InvalidConfiguration, match="approved"):
        activate_version(ADMIN, tested["id"], "Cannot skip approval")
    with pytest.raises(InvalidConfiguration, match="approved successor"):
        supersede_version(ADMIN, active["id"], tested["id"], "Cannot use tested successor")


def test_only_canonically_assigned_human_administrator_can_govern_without_partial_mutation():
    before = governance_fingerprint()
    with pytest.raises(ForbiddenError):
        certify_draft(PREPARER, CONTRACT, "Unauthorized test")
    assert governance_fingerprint() == before

    tested = certify_draft(ADMIN, CONTRACT, "Candidate for authority denial")
    fabricated = Actor("system-ai", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
    before = governance_fingerprint()
    with pytest.raises(ForbiddenError):
        approve_version(fabricated, tested["id"], "AI approval attempt")
    assert governance_fingerprint() == before


def test_configuration_contract_rejects_missing_deterministic_rule():
    payload = draft_payload()
    payload["rules"] = payload["rules"][:-1]
    with pytest.raises(InvalidConfiguration, match="five deterministic"):
        update_draft(ADMIN, CONTRACT, payload)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("invalid_service_date", "ISO service period"),
        ("invalid_category_limit", "must be a decimal"),
        ("nonfinite_control_total", "finite nonnegative"),
        ("nonboolean_rule", "five deterministic"),
        ("fractional_day_window", "nonnegative integer"),
        ("nonboolean_package_flag", "Package labels and settings"),
        ("duplicate_evidence", "At least one evidence type"),
    ],
)
def test_semantically_invalid_configuration_cannot_be_saved(case, expected):
    payload = draft_payload()
    if case == "invalid_service_date":
        payload["servicePeriod"]["start"] = "06/01/2026"
    elif case == "invalid_category_limit":
        payload["categories"][0]["limit"] = "not-a-number"
    elif case == "nonfinite_control_total":
        payload["ledgerControlTotal"] = "NaN"
    elif case == "nonboolean_rule":
        payload["rules"][0]["enabled"] = "yes"
    elif case == "fractional_day_window":
        payload["rules"][-1]["dayWindow"] = 1.5
    elif case == "nonboolean_package_flag":
        payload["package"]["includeManifest"] = "yes"
    else:
        payload["requiredEvidence"].append(payload["requiredEvidence"][0])
    before = governance_fingerprint()
    with pytest.raises(InvalidConfiguration, match=expected):
        update_draft(ADMIN, CONTRACT, payload)
    assert governance_fingerprint() == before


def test_invoice_and_validation_records_require_exact_historical_configuration_version():
    active = active_summary(ADMIN, CONTRACT)
    with database() as connection:
        connection.execute(
            "insert into invoice_versions(id, contract_id, version, configuration_version_id) values ('invoice-v1', %s, 1, %s)",
            (CONTRACT, active["id"]),
        )
        connection.execute(
            "insert into validation_runs(id, invoice_version_id, configuration_version_id) values ('validation-v1', 'invoice-v1', %s)",
            (active["id"],),
        )
        connection.commit()
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with database() as connection:
            connection.execute(
                "insert into invoice_versions(id, contract_id, version, configuration_version_id) values ('invoice-bad', %s, 99, 'missing-config')",
                (CONTRACT,),
            )


def test_bounded_admin_draft_and_active_summary_for_later_personas():
    payload = draft_payload()
    payload["categories"][0]["limit"] = "61000.00"
    payload["rules"][-1]["dayWindow"] = 2
    payload["workflowLabels"]["submitted"] = "Agency review queue"
    payload["package"]["label"] = "Configured demo package"
    update_draft(ADMIN, CONTRACT, payload)
    assert get_draft(ADMIN, CONTRACT)["categories"][0]["limit"] == "61000.00"
    active = active_summary(ADMIN, CONTRACT)
    for actor in (PREPARER, GOVERNMENT):
        summary = active_summary(actor, CONTRACT)
        assert summary["id"] == active["id"]
        assert summary["version"] == active["version"]
        assert summary["activatedAt"]
    with pytest.raises(ForbiddenError):
        get_draft(PREPARER, CONTRACT)
    with pytest.raises(ForbiddenError):
        active_summary(AUDITOR, CONTRACT)
