from copy import deepcopy
import json
import uuid

from .access_scope import configuration_scope
from .authorization import Action, Actor, execute_authorized, require_permission
from .runtime import database
from .provenance import append_event_tx

REQUIRED_RULES = {"SERVICE_PERIOD", "REQUIRED_EVIDENCE", "BUDGET_AVAILABLE", "TOTAL_RECONCILIATION", "POSSIBLE_DUPLICATE"}
REQUIRED_WORKFLOW_LABELS = {"draft", "submitted", "returned", "approved"}


class InvalidConfiguration(ValueError):
    pass


def validate_configuration(payload: dict) -> None:
    period = payload.get("servicePeriod", {})
    if not period.get("start") or not period.get("end") or period["start"] > period["end"]:
        raise InvalidConfiguration("A valid service period is required")
    categories = payload.get("categories", [])
    if not categories or any(not {"code", "label", "limit"} <= item.keys() for item in categories):
        raise InvalidConfiguration("Categories with labels and limits are required")
    if not payload.get("requiredEvidence"):
        raise InvalidConfiguration("At least one evidence type is required")
    rules = {rule.get("code"): rule for rule in payload.get("rules", [])}
    if set(rules) != REQUIRED_RULES or any(rule.get("severity") not in {"blocker", "warning"} for rule in rules.values()):
        raise InvalidConfiguration("The five deterministic POC rules must be configured")
    duplicate = rules["POSSIBLE_DUPLICATE"]
    if "amountTolerance" not in duplicate or "dayWindow" not in duplicate:
        raise InvalidConfiguration("Duplicate warning parameters are required")
    if not REQUIRED_WORKFLOW_LABELS <= payload.get("workflowLabels", {}).keys():
        raise InvalidConfiguration("All workflow labels are required")
    package = payload.get("package", {})
    if not package.get("label") or not package.get("invoiceTitle"):
        raise InvalidConfiguration("Package labels and settings are required")


def update_draft(actor: Actor, contract_id: str, payload: dict) -> dict:
    validate_configuration(payload)
    snapshot = deepcopy(payload)
    snapshot["status"] = "draft"

    def command():
        with database() as connection:
            connection.execute(
                """insert into configuration_drafts(contract_id, payload, updated_by)
                   values (%s, %s, %s)
                   on conflict (contract_id) do update set payload=excluded.payload,
                   updated_by=excluded.updated_by, updated_at=now()""",
                (contract_id, json.dumps(snapshot), actor.user_id),
            )
            connection.commit()
        return snapshot

    return execute_authorized(actor, Action.UPDATE, configuration_scope(actor, contract_id), command)


def activate_draft(actor: Actor, contract_id: str) -> dict:
    def command():
        with database() as connection:
            row = connection.execute("select payload from configuration_drafts where contract_id=%s", (contract_id,)).fetchone()
            if not row:
                raise InvalidConfiguration("No draft exists")
            payload = deepcopy(row[0])
            validate_configuration(payload)
            next_version = connection.execute(
                "select coalesce(max(version), 0) + 1 from configuration_versions where contract_id=%s", (contract_id,)
            ).fetchone()[0]
            version_id = f"config-{contract_id}-v{next_version}-{uuid.uuid4().hex[:8]}"
            payload.update({"id": version_id, "version": next_version, "status": "active"})
            connection.execute(
                """insert into configuration_versions
                   (id, contract_id, version, status, payload, activated_by, activated_at)
                   values (%s,%s,%s,'active',%s,%s,now())""",
                (version_id, contract_id, next_version, json.dumps(payload), actor.user_id),
            )
            append_event_tx(connection, "config_activated", "configuration_version", version_id,
                            actor_id=actor.user_id, organization_id=actor.organization_id,
                            contract_id=contract_id, payload={"version": next_version})
            connection.commit()
        return payload

    return execute_authorized(actor, Action.ACTIVATE, configuration_scope(actor, contract_id), command)


def get_draft(actor: Actor, contract_id: str) -> dict:
    require_permission(actor,Action.READ,configuration_scope(actor,contract_id))
    with database() as connection:
        row=connection.execute("select payload from configuration_drafts where contract_id=%s",(contract_id,)).fetchone()
    if not row: raise InvalidConfiguration("No draft exists")
    return row[0]


def active_summary(actor: Actor, contract_id: str) -> dict | None:
    require_permission(actor,Action.READ,configuration_scope(actor,contract_id,active_only=True))
    with database() as connection:
        row=connection.execute("select id,version,activated_at from configuration_versions where contract_id=%s order by version desc limit 1",(contract_id,)).fetchone()
    return {"id":row[0],"version":row[1],"activatedAt":row[2].isoformat()} if row else None
