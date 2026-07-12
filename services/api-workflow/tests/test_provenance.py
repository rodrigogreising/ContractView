import json
from hashlib import sha256
from pathlib import Path
import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.artifacts import store_artifact
from app.authentication import authenticate, revoke_session
from app.authorization import Actor, ForbiddenError, Role
from configuration_helpers import ensure_active_configuration
from app.provenance import EVENT_TYPES, LineageInput, append_event, append_lineage, append_relation_tx, audit_query
from app.http.api import app
from app.application.transaction import transaction as application_database
from app.runtime import database

CONTRACT = "contract-synthetic-agency-ngo-2026"
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
GOVERNMENT = Actor("user-government-reviewer", "org-government", Role.GOVERNMENT_REVIEWER)
OTHER_NGO = Actor("outside-user", "org-outside", Role.NGO_PREPARER)


def _ensure_submitted_contract() -> None:
    with database() as connection:
        config = connection.execute(
            "select configuration_version_id from configuration_active_versions where contract_id=%s",
            (CONTRACT,),
        ).fetchone()
    if not config:
        config = (ensure_active_configuration(ADMIN, CONTRACT)["id"],)
    with database() as connection:
        version = connection.execute(
            "select coalesce(max(version),0)+1 from invoice_versions where contract_id=%s",
            (CONTRACT,),
        ).fetchone()[0]
        connection.execute(
            """insert into invoice_versions
               (id,contract_id,version,configuration_version_id,state,organization_id,created_by,total)
               values (%s,%s,%s,%s,'submitted','org-ngo','user-ngo-approver',0)""",
            (f"audit-submitted-{uuid.uuid4().hex}", CONTRACT, version, config[0]),
        )
        connection.commit()


def test_all_canonical_material_event_types_are_appendable_and_ordered():
    _ensure_submitted_contract()
    material = EVENT_TYPES - {"login_succeeded", "login_failed", "logout"}
    ids = [append_event(event, "demo", f"aggregate-{event}", actor_id=PREPARER.user_id,
                        organization_id=PREPARER.organization_id, contract_id=CONTRACT,
                        payload={"test": event}) for event in sorted(material)]
    assert ids == sorted(ids)
    audit = audit_query(PREPARER, CONTRACT, submitted=True)
    recorded = {event["eventType"] for event in audit["events"]}
    assert material <= recorded
    emitted = [event for event in audit["events"] if event["id"] in ids]
    assert all(event["schemaVersion"] == 1 for event in emitted)
    assert all(event["actorId"] == PREPARER.user_id for event in emitted)
    assert all(event["actorRole"] == Role.NGO_PREPARER.value for event in emitted)
    assert all(event["actorOrganizationId"] == PREPARER.organization_id for event in emitted)
    assert all(event["organizationId"] == PREPARER.organization_id for event in emitted)
    assert all(event["versionReferences"] for event in emitted)
    assert all(len(event["eventHash"]) == 64 for event in emitted)
    for event in emitted:
        envelope = {
            "eventId": event["eventKey"],
            "eventType": event["eventType"],
            "schemaVersion": event["schemaVersion"],
            "actorId": event["actorId"],
            "actorRole": event["actorRole"],
            "actorOrganizationId": event["actorOrganizationId"],
            "organizationId": event["organizationId"],
            "contractId": event["contractId"],
            "aggregateType": event["aggregateType"],
            "aggregateId": event["aggregateId"],
            "payload": event["payload"],
            "reasonCode": event["reasonCode"],
            "versionReferences": event["versionReferences"],
        }
        canonical = json.dumps(envelope,sort_keys=True,separators=(",",":"),default=str)
        assert event["eventHash"] == sha256(canonical.encode()).hexdigest()


def test_database_rejects_an_incomplete_material_event_envelope():
    with pytest.raises(psycopg.errors.RaiseException, match="material events require"):
        with database() as connection:
            connection.execute(
                "insert into domain_events(event_type,aggregate_type,aggregate_id) values ('validation_completed','validation_run','incomplete')"
            )


def test_relation_actor_must_match_canonical_identity_without_mutation():
    with database() as connection:
        before = connection.execute("select count(*) from provenance_relations").fetchone()[0]
    forged = Actor(PREPARER.user_id, PREPARER.organization_id, Role.NGO_APPROVER)
    with pytest.raises(ValueError, match="canonical identity"):
        with application_database() as connection:
            append_relation_tx(
                connection,
                CONTRACT,
                PREPARER.organization_id,
                "supports",
                {"kind":"artifact","id":"forged-source","version":1},
                {"kind":"invoice","id":"forged-target","version":1},
                actor=forged,
            )
    with database() as connection:
        after = connection.execute("select count(*) from provenance_relations").fetchone()[0]
    assert after == before


def test_auditor_query_excludes_draft_only_events_after_contract_submission():
    _ensure_submitted_contract()
    with database() as connection:
        config = connection.execute(
            "select configuration_version_id from configuration_active_versions where contract_id=%s",
            (CONTRACT,),
        ).fetchone()[0]
        version = connection.execute(
            "select coalesce(max(version),0)+1 from invoice_versions where contract_id=%s",
            (CONTRACT,),
        ).fetchone()[0]
        draft_id = f"auditor-hidden-draft-{uuid.uuid4().hex}"
        connection.execute(
            """insert into invoice_versions
               (id,contract_id,version,configuration_version_id,state,organization_id,created_by,total)
               values (%s,%s,%s,%s,'draft','org-ngo','user-ngo-preparer',0)""",
            (draft_id, CONTRACT, version, config),
        )
        connection.commit()
    append_event("revision_created", "invoice_version", draft_id, actor_id=PREPARER.user_id,
                 organization_id=PREPARER.organization_id, contract_id=CONTRACT)
    assert draft_id in {item["aggregateId"] for item in audit_query(PREPARER, CONTRACT, submitted=True)["events"]}
    assert draft_id not in {item["aggregateId"] for item in audit_query(AUDITOR, CONTRACT, submitted=True)["events"]}


def test_authentication_and_logout_append_domain_events():
    token, _, _ = authenticate("ngo.preparer@example.test", "Demo-Prepare-2026!")
    revoke_session(token)
    with database() as connection:
        events = connection.execute(
            "select event_type from domain_events where actor_id=%s order by id desc limit 2",
            (PREPARER.user_id,),
        ).fetchall()
    assert [row[0] for row in events] == ["logout", "login_succeeded"]


def test_field_lineage_connects_source_extraction_correction_rule_invoice_and_package():
    _ensure_submitted_contract()
    active = ensure_active_configuration(ADMIN, CONTRACT)
    source = store_artifact(PREPARER, CONTRACT, "receipt.png", "image/png", b"receipt-source")
    package = store_artifact(PREPARER, CONTRACT, "package.zip", "application/zip", b"package-v1", artifact_kind="generated")
    with database() as connection:
        invoice_number = connection.execute(
            "select coalesce(max(version), 0) + 1 from invoice_versions where contract_id=%s", (CONTRACT,)
        ).fetchone()[0]
        connection.execute(
            """insert into invoice_versions
               (id,contract_id,version,configuration_version_id,state,organization_id,created_by,total)
               values ('prov-invoice-v1',%s,%s,%s,'submitted','org-ngo','user-ngo-approver',0)""",
            (CONTRACT, invoice_number, active["id"]),
        )
        connection.execute(
            "insert into validation_runs(id, invoice_version_id, configuration_version_id) values ('prov-validation-v1','prov-invoice-v1',%s)",
            (active["id"],),
        )
        connection.commit()
    proposed = append_lineage(LineageInput(
        CONTRACT, "org-ngo", "claimedAmount", "119.00", source.id, "page=1;bbox=10,20,30,40",
        "ledger-importer-v1", "replaceable-demo-provider", "draft-model-v1", "prompt-v1", "parser-v1",
        "mapping-v1", validation_run_id="prov-validation-v1", invoice_version_id="prov-invoice-v1",
    ))
    corrected = append_lineage(LineageInput(
        CONTRACT, "org-ngo", "claimedAmount", "120.00", source.id, "page=1;bbox=10,20,30,40",
        "ledger-importer-v1", "replaceable-demo-provider", "draft-model-v1", "prompt-v1", "parser-v1",
        "mapping-v1", PREPARER.user_id, "Corrected against visible total", "prov-validation-v1",
        "prov-invoice-v1", package.id, proposed,
    ))
    audit = audit_query(AUDITOR, CONTRACT, submitted=True)
    lineage = [item for item in audit["lineage"] if item["id"] in {proposed, corrected}]
    assert lineage[0]["fieldValue"] == "119.00"
    assert lineage[1]["fieldValue"] == "120.00"
    assert lineage[1]["predecessorLineageId"] == proposed
    assert lineage[1]["sourceArtifactId"] == source.id
    assert lineage[1]["validationRunId"] == "prov-validation-v1"
    assert lineage[1]["packageArtifactId"] == package.id


def test_provenance_is_append_only_and_audit_query_is_authorized_read_only():
    _ensure_submitted_contract()
    event_id = append_event("validation_completed", "validation", "immutable-run",
                            actor_id=PREPARER.user_id, organization_id="org-ngo", contract_id=CONTRACT)
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        with database() as connection:
            connection.execute("update domain_events set payload='{}' where id=%s", (event_id,))
    assert audit_query(PREPARER, CONTRACT, submitted=False)["events"]
    assert audit_query(GOVERNMENT, CONTRACT, submitted=True)["events"]
    assert audit_query(GOVERNMENT, CONTRACT, submitted=False)["events"]
    with pytest.raises(ForbiddenError):
        audit_query(OTHER_NGO, CONTRACT, submitted=True)


def test_auditor_http_timeline_is_read_only_and_mutations_leave_no_trace():
    _ensure_submitted_contract()
    with database() as connection:
        invoice_id = connection.execute(
            "select id from invoice_versions where contract_id=%s and state='submitted' order by created_at desc limit 1",
            (CONTRACT,),
        ).fetchone()[0]
    with TestClient(app) as client:
        login = client.post("/auth/login", json={
            "email": "auditor@example.test", "password": "Demo-Audit-2026!",
        })
        assert login.status_code == 200
        protected_tables = (
            "configuration_versions", "configuration_test_evidence", "configuration_approvals",
            "configuration_lifecycle_events", "artifacts", "invoice_versions", "invoice_snapshots",
            "validation_runs", "attestations", "packages", "package_artifacts", "submissions",
            "government_queue_items", "government_decisions", "revision_corrections",
            "provenance_relations", "field_lineage", "domain_events",
        )
        with database() as connection:
            before = tuple(connection.execute(f"select count(*) from {table}").fetchone()[0] for table in protected_tables)
        timeline = client.get(f"/audit/timeline?contractId={CONTRACT}")
        assert timeline.status_code == 200
        assert timeline.json()["contractId"] == CONTRACT
        denied = (
            client.post(f"/configuration/test?contractId={CONTRACT}", json={"rationale":"forbidden"}),
            client.post(f"/invoices/draft?contractId={CONTRACT}"),
            client.post(f"/invoices/{invoice_id}/validation"),
            client.post(f"/invoices/{invoice_id}/attest", json={"text":"forbidden"}),
            client.post(f"/invoices/{invoice_id}/package"),
            client.post(f"/invoices/{invoice_id}/submit"),
        )
        assert all(response.status_code == 403 for response in denied)
    with database() as connection:
        after = tuple(connection.execute(f"select count(*) from {table}").fetchone()[0] for table in protected_tables)
    assert after == before
