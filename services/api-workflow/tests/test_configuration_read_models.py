import json
from hashlib import sha256
from pathlib import Path
import uuid

import pytest

from app.authorization import Actor, ForbiddenError, Role
from app.configuration import (
    InvalidConfiguration,
    active_summary,
    activate_version,
    approve_version,
    compare_configuration_versions,
    configuration_activation_impact,
    configuration_references,
    configuration_version_detail,
    get_draft_details,
    supersede_version,
    test_draft as certify_draft,
    update_draft,
)
from app.runtime import database


FIXTURE = Path("/app/fixtures/scenario.json")
CONTRACT = "contract-synthetic-agency-ngo-2026"
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
GOVERNMENT = Actor("user-government-reviewer", "org-government", Role.GOVERNMENT_REVIEWER)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)


def _payload(label: str) -> dict:
    payload = json.loads(FIXTURE.read_text())["initialConfiguration"]
    payload["package"]["label"] = label
    return payload


def _hash(value: object) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _candidate(label: str) -> dict:
    draft = get_draft_details(ADMIN, CONTRACT)
    saved = update_draft(ADMIN, CONTRACT, _payload(label), draft["revision"])
    tested = certify_draft(
        ADMIN,
        CONTRACT,
        f"Deterministic fixture evaluation for {label}",
        saved["revision"],
    )
    approve_version(ADMIN, tested["id"], f"Human approval for {label}")
    return tested


def _activate(candidate: dict) -> None:
    current = active_summary(ADMIN, CONTRACT)
    if current:
        supersede_version(
            ADMIN,
            current["id"],
            candidate["id"],
            f"Prospective activation of version {candidate['version']}",
        )
    else:
        activate_version(
            ADMIN,
            candidate["id"],
            f"Prospective activation of version {candidate['version']}",
        )


def _draft_fingerprint() -> tuple:
    with database() as connection:
        return connection.execute(
            "select payload,revision,updated_by,updated_at from configuration_drafts where contract_id=%s",
            (CONTRACT,),
        ).fetchone()


def test_stale_draft_save_and_test_fail_before_mutation() -> None:
    initial = get_draft_details(ADMIN, CONTRACT)
    saved = update_draft(
        ADMIN,
        CONTRACT,
        _payload("Current optimistic draft"),
        initial["revision"],
    )
    after_save = _draft_fingerprint()

    with pytest.raises(InvalidConfiguration, match="revision is stale"):
        update_draft(
            ADMIN,
            CONTRACT,
            _payload("Rejected stale draft"),
            initial["revision"],
        )
    assert _draft_fingerprint() == after_save

    with database() as connection:
        before_versions = connection.execute(
            "select count(*) from configuration_versions"
        ).fetchone()[0]
    with pytest.raises(InvalidConfiguration, match="revision is stale"):
        certify_draft(
            ADMIN,
            CONTRACT,
            "Rejected stale deterministic test",
            initial["revision"],
        )
    with database() as connection:
        assert connection.execute(
            "select count(*) from configuration_versions"
        ).fetchone()[0] == before_versions
    assert get_draft_details(ADMIN, CONTRACT)["revision"] == saved["revision"]


def test_derived_diff_impact_and_runtime_references_are_replayable_and_historical() -> None:
    first = _candidate("Immutable historical package definition")
    _activate(first)

    suffix = uuid.uuid4().hex
    invoice_id = f"invoice-config-ref-{suffix}"
    validation_id = f"validation-config-ref-{suffix}"
    attestation_id = f"attestation-config-ref-{suffix}"
    package_id = f"package-config-ref-{suffix}"
    submission_id = f"submission-config-ref-{suffix}"
    snapshot_id = f"snapshot-config-ref-{suffix}"
    with database() as connection:
        invoice_version = connection.execute(
            "select coalesce(max(version),0)+1 from invoice_versions where contract_id=%s",
            (CONTRACT,),
        ).fetchone()[0]
        connection.execute(
            "insert into invoice_versions(id,contract_id,version,configuration_version_id,state,organization_id,created_by,total) values (%s,%s,%s,%s,'submitted','org-ngo','user-ngo-approver',10)",
            (invoice_id, CONTRACT, invoice_version, first["id"]),
        )
        connection.execute(
            "insert into validation_runs(id,invoice_version_id,configuration_version_id,engine_version,status,created_by,material_revision) values (%s,%s,%s,'deterministic-validation-v1','completed','user-ngo-preparer',1)",
            (validation_id, invoice_id, first["id"]),
        )
        connection.execute(
            "insert into attestations(id,invoice_version_id,validation_run_id,material_revision,invoice_fingerprint,actor_id,actor_role,attestation_version,attestation_text) values (%s,%s,%s,1,%s,'user-ngo-approver','ngo_approver','v1','Synthetic attestation')",
            (attestation_id, invoice_id, validation_id, "a" * 64),
        )
        connection.execute(
            "insert into packages(id,invoice_version_id,attestation_id,version,manifest,created_by) values (%s,%s,%s,1,'{}','user-ngo-approver')",
            (package_id, invoice_id, attestation_id),
        )
        connection.execute(
            "insert into submissions(id,invoice_version_id,package_id,actor_id,actor_role,configuration_version_id,invoice_version,package_hashes) values (%s,%s,%s,'user-ngo-approver','ngo_approver',%s,%s,'{}')",
            (submission_id, invoice_id, package_id, first["id"], invoice_version),
        )
        connection.execute(
            "insert into invoice_snapshots(id,invoice_version_id,contract_id,organization_id,invoice_version,material_revision,stage,payload,snapshot_hash,created_by,actor_role) values (%s,%s,%s,'org-ngo',%s,1,'submission','{}',%s,'user-ngo-approver','ngo_approver')",
            (snapshot_id, invoice_id, CONTRACT, invoice_version, "b" * 64),
        )
        connection.commit()

    second = _candidate("Prospective successor package definition")
    impact = configuration_activation_impact(ADMIN, second["id"])
    assert impact["wouldSupersedeVersionId"] == first["id"]
    assert impact["historicalReferenceVersionId"] == first["id"]
    assert impact["applicationScope"] == "future-intake-only"
    assert impact["historicalReferencesPreserved"] is True
    assert impact["referenceCounts"]["invoice"] == 1
    assert impact["referenceCounts"]["submission"] == 1
    impact_body = {key: value for key, value in impact.items() if key != "projectionHash"}
    assert impact["projectionHash"] == _hash(impact_body)

    comparison = compare_configuration_versions(ADMIN, first["id"], second["id"])
    replayed_comparison = compare_configuration_versions(ADMIN, first["id"], second["id"])
    assert comparison == replayed_comparison
    comparison_body = {key: value for key, value in comparison.items() if key != "projectionHash"}
    assert comparison["projectionHash"] == _hash(comparison_body)
    assert comparison["canonical"] is False
    assert any(
        change["path"] == "/package/label" and change["changeType"] == "changed"
        for change in comparison["changes"]
    )

    _activate(second)
    references = configuration_references(ADMIN, first["id"])
    assert references == configuration_references(ADMIN, first["id"])
    references_body = {key: value for key, value in references.items() if key != "projectionHash"}
    assert references["projectionHash"] == _hash(references_body)
    assert references["canonical"] is False
    kinds = {reference["resourceKind"] for reference in references["references"]}
    assert {
        "invoice",
        "validation_run",
        "package",
        "submission",
        "invoice_snapshot",
        "audit_event",
    } <= kinds

    historical = configuration_version_detail(ADMIN, first["id"])
    assert historical["state"] == "superseded"
    assert historical["configuration"]["package"]["label"] == "Immutable historical package definition"
    assert active_summary(ADMIN, CONTRACT)["id"] == second["id"]


def test_configuration_read_models_and_mutations_remain_canonically_scoped() -> None:
    candidate = _candidate("Authorization projection candidate")
    _activate(candidate)
    unassigned_admin = Actor(
        "user-ngo-preparer",
        "org-ngo",
        Role.CONFIGURATION_ADMINISTRATOR,
    )
    for actor in (PREPARER, GOVERNMENT, AUDITOR, unassigned_admin):
        with pytest.raises(ForbiddenError):
            configuration_version_detail(actor, candidate["id"])
        with pytest.raises(ForbiddenError):
            configuration_references(actor, candidate["id"])
        with pytest.raises(ForbiddenError):
            configuration_activation_impact(actor, candidate["id"])
    assert active_summary(PREPARER, CONTRACT)["id"] == candidate["id"]
    assert active_summary(GOVERNMENT, CONTRACT)["id"] == candidate["id"]


def test_activation_revalidates_current_successful_test_and_approval_evidence() -> None:
    payload = _payload("Failed deterministic evidence")
    payload_hash = _hash(payload)
    report = {
        "suiteVersion": "configuration-governance-v1",
        "passed": False,
        "checks": [{"code": "SERVICE_PERIOD", "passed": False}],
    }
    result_hash = _hash({"payloadHash": payload_hash, "report": report})
    suffix = uuid.uuid4().hex
    version_id = f"config-invalid-evidence-{suffix}"
    evidence_id = f"config-invalid-test-{suffix}"
    approval_id = f"config-invalid-approval-{suffix}"
    with database() as connection:
        version = connection.execute(
            "select coalesce(max(version),0)+1 from configuration_versions where contract_id=%s",
            (CONTRACT,),
        ).fetchone()[0]
        snapshot = {**payload, "id": version_id, "version": version, "status": "tested"}
        approval_body = {
            "id": approval_id,
            "configurationVersionId": version_id,
            "testEvidenceId": evidence_id,
            "approvedBy": ADMIN.user_id,
            "approvedRole": ADMIN.role.value,
            "approvedOrganizationId": ADMIN.organization_id,
            "rationale": "Synthetic invalid evidence fixture",
        }
        connection.execute(
            "insert into configuration_versions(id,contract_id,version,status,payload) values (%s,%s,%s,'tested',%s)",
            (version_id, CONTRACT, version, json.dumps(snapshot)),
        )
        connection.execute(
            "insert into configuration_test_evidence(id,configuration_version_id,contract_id,payload_hash,suite_version,results,result_hash,tested_by,tested_role,tested_organization_id,rationale) values (%s,%s,%s,%s,'configuration-governance-v1',%s,%s,%s,%s,%s,'Synthetic failed test')",
            (
                evidence_id,
                version_id,
                CONTRACT,
                payload_hash,
                json.dumps(report),
                result_hash,
                ADMIN.user_id,
                ADMIN.role.value,
                ADMIN.organization_id,
            ),
        )
        connection.execute(
            "insert into configuration_approvals(id,configuration_version_id,contract_id,test_evidence_id,approved_by,approved_role,approved_organization_id,rationale,approval_hash) values (%s,%s,%s,%s,%s,%s,%s,'Synthetic invalid evidence fixture',%s)",
            (
                approval_id,
                version_id,
                CONTRACT,
                evidence_id,
                ADMIN.user_id,
                ADMIN.role.value,
                ADMIN.organization_id,
                _hash(approval_body),
            ),
        )
        for state, action, event_approval in (
            ("tested", "test", None),
            ("approved", "approve_configuration", approval_id),
        ):
            connection.execute(
                "insert into configuration_lifecycle_events(id,configuration_version_id,contract_id,state,action,actor_id,actor_role,actor_organization_id,rationale,test_evidence_id,approval_id,event_hash) values (%s,%s,%s,%s,%s,%s,%s,%s,'Synthetic invalid evidence fixture',%s,%s,%s)",
                (
                    f"config-invalid-event-{state}-{suffix}",
                    version_id,
                    CONTRACT,
                    state,
                    action,
                    ADMIN.user_id,
                    ADMIN.role.value,
                    ADMIN.organization_id,
                    evidence_id,
                    event_approval,
                    ("c" if state == "tested" else "d") * 64,
                ),
            )
        connection.commit()
    before = active_summary(ADMIN, CONTRACT)
    with pytest.raises(InvalidConfiguration, match="successful deterministic test evidence"):
        activate_version(ADMIN, version_id, "Activation must reject failed evidence")
    assert active_summary(ADMIN, CONTRACT) == before


def test_migration_installs_revision_and_reference_indexes_without_projection_tables() -> None:
    with database() as connection:
        revision = connection.execute(
            "select is_nullable,column_default from information_schema.columns where table_name='configuration_drafts' and column_name='revision'"
        ).fetchone()
        indexes = {
            row[0]
            for row in connection.execute(
                "select indexname from pg_indexes where schemaname='public' and indexname in ('invoice_versions_configuration_reference_idx','validation_runs_configuration_reference_idx','submissions_configuration_reference_idx','domain_events_version_references_idx')"
            ).fetchall()
        }
        projection_tables = connection.execute(
            "select count(*) from information_schema.tables where table_schema='public' and table_name like 'configuration_%projection%'"
        ).fetchone()[0]
    assert revision[0] == "NO"
    assert revision[1] == "1"
    assert indexes == {
        "invoice_versions_configuration_reference_idx",
        "validation_runs_configuration_reference_idx",
        "submissions_configuration_reference_idx",
        "domain_events_version_references_idx",
    }
    assert projection_tables == 0
