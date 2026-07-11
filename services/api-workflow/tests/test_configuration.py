import json
from pathlib import Path

import psycopg
import pytest

from app.authorization import Actor, ForbiddenError, Role
from app.configuration import InvalidConfiguration, activate_draft, active_summary, get_draft, update_draft
from app.runtime import database

FIXTURE = Path("/app/fixtures/scenario.json")
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
GOVERNMENT = Actor("user-government-reviewer","org-government",Role.GOVERNMENT_REVIEWER)
AUDITOR = Actor("user-auditor","org-oversight",Role.AUDITOR)
CONTRACT = "contract-metro-harbor-2026"


def draft_payload():
    return json.loads(FIXTURE.read_text())["initialConfiguration"]


def test_draft_is_editable_and_activation_creates_numbered_immutable_snapshots():
    payload = draft_payload()
    payload["package"]["label"] = "First activated package"
    update_draft(ADMIN, CONTRACT, payload)
    version_one = activate_draft(ADMIN, CONTRACT)
    assert version_one["version"] == 1
    assert version_one["package"]["label"] == "First activated package"

    payload["package"]["label"] = "Second activated package"
    update_draft(ADMIN, CONTRACT, payload)
    version_two = activate_draft(ADMIN, CONTRACT)
    assert version_two["version"] == 2
    assert version_two["id"] != version_one["id"]

    with database() as connection:
        stored = connection.execute(
            "select version, payload->'package'->>'label' from configuration_versions where contract_id=%s order by version",
            (CONTRACT,),
        ).fetchall()
    assert stored == [(1, "First activated package"), (2, "Second activated package")]

    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        with database() as connection:
            connection.execute("update configuration_versions set payload='{}' where id=%s", (version_one["id"],))


@pytest.mark.parametrize("operation", [update_draft, lambda actor, contract, payload: activate_draft(actor, contract)])
def test_only_configuration_administrator_can_edit_or_activate(operation):
    before = None
    with database() as connection:
        before = connection.execute("select count(*) from configuration_versions").fetchone()[0]
    with pytest.raises(ForbiddenError):
        operation(PREPARER, CONTRACT, draft_payload())
    with database() as connection:
        after = connection.execute("select count(*) from configuration_versions").fetchone()[0]
    assert after == before


def test_configuration_contract_rejects_missing_deterministic_rule():
    payload = draft_payload()
    payload["rules"] = payload["rules"][:-1]
    with pytest.raises(InvalidConfiguration, match="five deterministic"):
        update_draft(ADMIN, CONTRACT, payload)


def test_invoice_and_validation_records_require_exact_configuration_version():
    active = activate_draft(ADMIN, CONTRACT)
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


def test_bounded_admin_draft_and_active_version_summary_for_later_personas():
    payload=draft_payload()
    payload["categories"][0]["limit"]="61000.00"
    payload["rules"][-1]["dayWindow"]=2
    payload["workflowLabels"]["submitted"]="Agency review queue"
    payload["package"]["label"]="Configured demo package"
    update_draft(ADMIN,CONTRACT,payload)
    assert get_draft(ADMIN,CONTRACT)["categories"][0]["limit"]=="61000.00"
    active=activate_draft(ADMIN,CONTRACT)
    for actor in (PREPARER,GOVERNMENT,AUDITOR):
        summary=active_summary(actor,CONTRACT)
        assert summary["id"]==active["id"] and summary["version"]==active["version"] and summary["activatedAt"]
    with pytest.raises(ForbiddenError): get_draft(PREPARER,CONTRACT)
