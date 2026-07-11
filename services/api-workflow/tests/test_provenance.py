import json
from pathlib import Path

import psycopg
import pytest

from app.artifacts import store_artifact
from app.authentication import authenticate, revoke_session
from app.authorization import Actor, ForbiddenError, Role
from app.configuration import activate_draft
from app.provenance import EVENT_TYPES, LineageInput, append_event, append_lineage, audit_query
from app.runtime import database

CONTRACT = "contract-metro-harbor-2026"
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
AUDITOR = Actor("user-auditor", "org-oversight", Role.AUDITOR)
GOVERNMENT = Actor("user-government-reviewer", "org-government", Role.GOVERNMENT_REVIEWER)
OTHER_NGO = Actor("outside-user", "org-outside", Role.NGO_PREPARER)


def test_all_canonical_material_event_types_are_appendable_and_ordered():
    material = EVENT_TYPES - {"login_succeeded", "login_failed", "logout"}
    ids = [append_event(event, "demo", f"aggregate-{event}", actor_id=PREPARER.user_id,
                        organization_id=PREPARER.organization_id, contract_id=CONTRACT,
                        payload={"test": event}) for event in sorted(material)]
    assert ids == sorted(ids)
    audit = audit_query(AUDITOR, CONTRACT, submitted=True)
    recorded = {event["eventType"] for event in audit["events"]}
    assert material <= recorded


def test_authentication_and_logout_append_domain_events():
    token, _, _ = authenticate("ngo.preparer@contractview.demo", "Demo-Prepare-2026!")
    revoke_session(token)
    with database() as connection:
        events = connection.execute(
            "select event_type from domain_events where actor_id=%s order by id desc limit 2",
            (PREPARER.user_id,),
        ).fetchall()
    assert [row[0] for row in events] == ["logout", "login_succeeded"]


def test_field_lineage_connects_source_extraction_correction_rule_invoice_and_package():
    active = activate_draft(ADMIN, CONTRACT)
    source = store_artifact(PREPARER, CONTRACT, "receipt.png", "image/png", b"receipt-source")
    package = store_artifact(PREPARER, CONTRACT, "package.zip", "application/zip", b"package-v1", artifact_kind="generated")
    with database() as connection:
        invoice_number = connection.execute(
            "select coalesce(max(version), 0) + 1 from invoice_versions where contract_id=%s", (CONTRACT,)
        ).fetchone()[0]
        connection.execute(
            "insert into invoice_versions(id, contract_id, version, configuration_version_id) values ('prov-invoice-v1',%s,%s,%s)",
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
    event_id = append_event("validation_completed", "validation", "immutable-run",
                            actor_id=PREPARER.user_id, organization_id="org-ngo", contract_id=CONTRACT)
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        with database() as connection:
            connection.execute("update domain_events set payload='{}' where id=%s", (event_id,))
    assert audit_query(PREPARER, CONTRACT, submitted=False)["events"]
    assert audit_query(GOVERNMENT, CONTRACT, submitted=True)["events"]
    with pytest.raises(ForbiddenError):
        audit_query(GOVERNMENT, CONTRACT, submitted=False)
    with pytest.raises(ForbiddenError):
        audit_query(OTHER_NGO, CONTRACT, submitted=True)
