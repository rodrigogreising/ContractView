from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import uuid

from .access_scope import configuration_scope
from ...authorization import Action, Actor, execute_authorized, require_permission
from .provenance import append_event_tx
from ...shared_contracts import ActiveConfigurationDto, ConfigurationLifecycleResponseDto

from ..ports.statements import Statement
from ..transaction import transaction as database

REQUIRED_RULES = {
    "SERVICE_PERIOD",
    "REQUIRED_EVIDENCE",
    "BUDGET_AVAILABLE",
    "TOTAL_RECONCILIATION",
    "POSSIBLE_DUPLICATE",
}
REQUIRED_WORKFLOW_LABELS = {"draft", "submitted", "returned", "approved"}
TEST_SUITE_VERSION = "configuration-governance-v1"
EVENT_TYPES = {
    "test": "config_tested",
    "approve_configuration": "config_approved",
    "activate": "config_activated",
    "supersede": "config_superseded",
    "retire": "config_retired",
    "rollback": "config_rollback_prepared",
}


class InvalidConfiguration(ValueError):
    pass


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: object) -> str:
    return sha256(_canonical(value).encode()).hexdigest()


def _rationale(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidConfiguration("A governance rationale is required")
    return normalized


def _nonnegative_decimal(value: object, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InvalidConfiguration(f"{field} must be a decimal") from None
    if not number.is_finite() or number < 0:
        raise InvalidConfiguration(f"{field} must be a finite nonnegative decimal")
    return number


def validate_configuration(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise InvalidConfiguration("Configuration must be an object")
    period = payload.get("servicePeriod", {})
    try:
        start = date.fromisoformat(period["start"])
        end = date.fromisoformat(period["end"])
    except (KeyError, TypeError, ValueError):
        raise InvalidConfiguration("A valid ISO service period is required") from None
    if start > end:
        raise InvalidConfiguration("A valid service period is required")
    categories = payload.get("categories", [])
    if not isinstance(categories, list) or not categories or any(
        not isinstance(item, dict)
        or not isinstance(item.get("code"), str)
        or not item["code"].strip()
        or not isinstance(item.get("label"), str)
        or not item["label"].strip()
        or "limit" not in item
        for item in categories
    ):
        raise InvalidConfiguration("Categories with labels and limits are required")
    category_codes = [item["code"] for item in categories]
    if len(category_codes) != len(set(category_codes)):
        raise InvalidConfiguration("Category codes must be unique")
    for item in categories:
        _nonnegative_decimal(item["limit"], f"Category {item['code']} limit")
    required_evidence = payload.get("requiredEvidence")
    if (
        not isinstance(required_evidence, list)
        or not required_evidence
        or any(not isinstance(item, str) or not item.strip() for item in required_evidence)
        or len(required_evidence) != len(set(required_evidence))
    ):
        raise InvalidConfiguration("At least one evidence type is required")
    if "ledgerControlTotal" not in payload:
        raise InvalidConfiguration("A ledger control total is required")
    _nonnegative_decimal(payload["ledgerControlTotal"], "Ledger control total")
    rule_list = payload.get("rules", [])
    if not isinstance(rule_list, list) or any(
        not isinstance(rule, dict) or not isinstance(rule.get("code"), str)
        for rule in rule_list
    ):
        raise InvalidConfiguration("The five deterministic POC rules must be configured")
    rules = {rule.get("code"): rule for rule in rule_list}
    if len(rule_list) != len(REQUIRED_RULES) or set(rules) != REQUIRED_RULES or any(
        rule.get("severity") not in {"blocker", "warning"}
        or not isinstance(rule.get("enabled"), bool)
        for rule in rules.values()
    ):
        raise InvalidConfiguration("The five deterministic POC rules must be configured")
    duplicate = rules["POSSIBLE_DUPLICATE"]
    if "amountTolerance" not in duplicate or "dayWindow" not in duplicate:
        raise InvalidConfiguration("Duplicate warning parameters are required")
    _nonnegative_decimal(duplicate["amountTolerance"], "Duplicate amount tolerance")
    day_window = duplicate["dayWindow"]
    if isinstance(day_window, bool) or not isinstance(day_window, int) or day_window < 0:
        raise InvalidConfiguration("Duplicate day window must be a nonnegative integer")
    workflow_labels = payload.get("workflowLabels", {})
    if (
        not isinstance(workflow_labels, dict)
        or set(workflow_labels) != REQUIRED_WORKFLOW_LABELS
        or any(not isinstance(label, str) or not label.strip() for label in workflow_labels.values())
    ):
        raise InvalidConfiguration("All workflow labels are required")
    package = payload.get("package", {})
    if (
        not isinstance(package, dict)
        or not isinstance(package.get("label"), str)
        or not package["label"].strip()
        or not isinstance(package.get("invoiceTitle"), str)
        or not package["invoiceTitle"].strip()
        or not isinstance(package.get("includeValidationSummary"), bool)
        or not isinstance(package.get("includeManifest"), bool)
    ):
        raise InvalidConfiguration("Package labels and settings are required")


def _test_report(payload: dict) -> dict:
    validate_configuration(payload)
    checks = [
        {"code": "SERVICE_PERIOD", "passed": True},
        {"code": "CATEGORY_SCHEMA", "passed": True},
        {"code": "EVIDENCE_REQUIREMENTS", "passed": True},
        {"code": "DETERMINISTIC_RULE_SET", "passed": True},
        {"code": "WORKFLOW_AND_TEMPLATE", "passed": True},
    ]
    return {
        "suiteVersion": TEST_SUITE_VERSION,
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
    }


def _details(connection, version_id: str) -> dict:
    row = connection.configuration.execute(
        Statement.CONFIGURATION_READ_CONFIGURATION_APPROVALS_CONFIGURATION_LIFECYCLE_EVENTS_CONFIGURATION_TEST_EVIDENCE_CONFIGURATION_VERSIONS_009,
        (version_id,),
    ).fetchone()
    if not row:
        raise InvalidConfiguration("Configuration version was not found")
    return {
        "id": version_id,
        "contractId": row[0],
        "version": row[1],
        "configuration": row[2],
        "state": row[3],
        "testEvidenceId": row[4],
        "payloadHash": row[5],
        "testResultHash": row[6],
        "testSuiteVersion": row[7],
        "approvalId": row[8],
        "approvalHash": row[9],
        "rollbackTargetId": row[10],
    }


def _append_lifecycle(
    connection,
    actor: Actor,
    *,
    version_id: str,
    contract_id: str,
    version: int,
    state: str,
    action: str,
    rationale: str,
    test_evidence_id: str | None = None,
    approval_id: str | None = None,
    predecessor_id: str | None = None,
    successor_id: str | None = None,
    rollback_target_id: str | None = None,
) -> dict:
    event_id = f"config-lifecycle-{uuid.uuid4().hex}"
    event_body = {
        "id": event_id,
        "configurationVersionId": version_id,
        "configurationVersion": version,
        "contractId": contract_id,
        "state": state,
        "action": action,
        "actorId": actor.user_id,
        "actorRole": actor.role.value,
        "actorOrganizationId": actor.organization_id,
        "rationale": rationale,
        "testEvidenceId": test_evidence_id,
        "approvalId": approval_id,
        "predecessorVersionId": predecessor_id,
        "successorVersionId": successor_id,
        "rollbackTargetVersionId": rollback_target_id,
    }
    event_hash = _hash(event_body)
    connection.configuration.execute(
        Statement.CONFIGURATION_WRITE_CONFIGURATION_LIFECYCLE_EVENTS_008,
        (
            event_id,
            version_id,
            contract_id,
            state,
            action,
            actor.user_id,
            actor.role.value,
            actor.organization_id,
            rationale,
            test_evidence_id,
            approval_id,
            predecessor_id,
            successor_id,
            rollback_target_id,
            event_hash,
        ),
    )
    append_event_tx(
        connection,
        EVENT_TYPES[action],
        "configuration_version",
        version_id,
        actor_id=actor.user_id,
        organization_id=actor.organization_id,
        contract_id=contract_id,
        payload={**event_body, "eventHash": event_hash},
    )
    return {**event_body, "eventHash": event_hash}


def _create_tested_version(
    connection,
    actor: Actor,
    contract_id: str,
    payload: dict,
    rationale: str,
    *,
    action: str,
    rollback_target_id: str | None = None,
) -> dict:
    snapshot = deepcopy(payload)
    for field in ("id", "version", "status"):
        snapshot.pop(field, None)
    validate_configuration(snapshot)
    payload_hash = _hash(snapshot)
    report = _test_report(snapshot)
    result_hash = _hash({"payloadHash": payload_hash, "report": report})
    next_version = connection.configuration.execute(
        Statement.CONFIGURATION_READ_CONFIGURATION_VERSIONS_003,
        (contract_id,),
    ).fetchone()[0]
    version_id = f"config-{contract_id}-v{next_version}-{uuid.uuid4().hex[:8]}"
    snapshot.update({"id": version_id, "version": next_version, "status": "tested"})
    evidence_id = f"config-test-{uuid.uuid4().hex}"
    connection.configuration.execute(
        Statement.CONFIGURATION_WRITE_CONFIGURATION_VERSIONS_004,
        (version_id, contract_id, next_version, json.dumps(snapshot)),
    )
    connection.configuration.execute(
        Statement.CONFIGURATION_WRITE_CONFIGURATION_TEST_EVIDENCE_007,
        (
            evidence_id,
            version_id,
            contract_id,
            payload_hash,
            TEST_SUITE_VERSION,
            json.dumps(report),
            result_hash,
            actor.user_id,
            actor.role.value,
            actor.organization_id,
            rationale,
        ),
    )
    _append_lifecycle(
        connection,
        actor,
        version_id=version_id,
        contract_id=contract_id,
        version=next_version,
        state="tested",
        action=action,
        rationale=rationale,
        test_evidence_id=evidence_id,
        rollback_target_id=rollback_target_id,
    )
    return {
        "id": version_id,
        "version": next_version,
        "state": "tested",
        "configuration": snapshot,
        "testEvidence": {
            "id": evidence_id,
            "suiteVersion": TEST_SUITE_VERSION,
            "payloadHash": payload_hash,
            "resultHash": result_hash,
            "passed": True,
        },
        "rollbackTargetId": rollback_target_id,
    }


def update_draft(actor: Actor, contract_id: str, payload: dict) -> dict:
    validate_configuration(payload)
    snapshot = deepcopy(payload)
    snapshot["status"] = "draft"

    def command():
        with database() as connection:
            connection.configuration.execute(
                Statement.CONFIGURATION_WRITE_CONFIGURATION_DRAFTS_001,
                (contract_id, json.dumps(snapshot), actor.user_id),
            )
            connection.commit()
        return snapshot

    return execute_authorized(
        actor,
        Action.UPDATE,
        configuration_scope(actor, contract_id),
        command,
    )


def activate_draft(actor: Actor, contract_id: str) -> dict:
    del actor, contract_id
    raise InvalidConfiguration(
        "Direct draft-to-active is prohibited; test, approve, and activate an immutable version"
    )


def test_draft(actor: Actor, contract_id: str, rationale: str) -> dict:
    rationale = _rationale(rationale)

    def command():
        with database() as connection:
            row = connection.configuration.execute(
                Statement.CONFIGURATION_READ_CONFIGURATION_DRAFTS_002,
                (contract_id,),
            ).fetchone()
            if not row:
                raise InvalidConfiguration("No draft exists")
            result = _create_tested_version(
                connection,
                actor,
                contract_id,
                row[0],
                rationale,
                action="test",
            )
            connection.commit()
        return result

    return execute_authorized(
        actor,
        Action.TEST,
        configuration_scope(actor, contract_id),
        command,
    )


def approve_version(actor: Actor, version_id: str, rationale: str) -> dict:
    rationale = _rationale(rationale)
    with database() as connection:
        version = _details(connection, version_id)

    def command():
        with database() as connection:
            current = _details(connection, version_id)
            if current["state"] != "tested" or not current["testEvidenceId"]:
                raise InvalidConfiguration("Only a tested version with immutable evidence may be approved")
            approval_id = f"config-approval-{uuid.uuid4().hex}"
            approval_body = {
                "id": approval_id,
                "configurationVersionId": version_id,
                "testEvidenceId": current["testEvidenceId"],
                "approvedBy": actor.user_id,
                "approvedRole": actor.role.value,
                "approvedOrganizationId": actor.organization_id,
                "rationale": rationale,
            }
            approval_hash = _hash(approval_body)
            connection.configuration.execute(
                Statement.CONFIGURATION_WRITE_CONFIGURATION_APPROVALS_011,
                (
                    approval_id,
                    version_id,
                    current["contractId"],
                    current["testEvidenceId"],
                    actor.user_id,
                    actor.role.value,
                    actor.organization_id,
                    rationale,
                    approval_hash,
                ),
            )
            _append_lifecycle(
                connection,
                actor,
                version_id=version_id,
                contract_id=current["contractId"],
                version=current["version"],
                state="approved",
                action="approve_configuration",
                rationale=rationale,
                test_evidence_id=current["testEvidenceId"],
                approval_id=approval_id,
                rollback_target_id=current["rollbackTargetId"],
            )
            connection.commit()
        return {**current, "state": "approved", "approvalId": approval_id, "approvalHash": approval_hash}

    return execute_authorized(
        actor,
        Action.APPROVE_CONFIGURATION,
        configuration_scope(actor, version["contractId"]),
        command,
    )


def activate_version(actor: Actor, version_id: str, rationale: str) -> dict:
    rationale = _rationale(rationale)
    with database() as connection:
        version = _details(connection, version_id)

    def command():
        with database() as connection:
            current = _details(connection, version_id)
            if current["state"] != "approved" or not current["approvalId"]:
                raise InvalidConfiguration("Only an approved version may be activated")
            active = connection.configuration.execute(
                Statement.CONFIGURATION_READ_CONFIGURATION_ACTIVE_VERSIONS_012,
                (current["contractId"],),
            ).fetchone()
            if active:
                raise InvalidConfiguration(
                    "Supersede the current active version with this approved successor"
                )
            connection.configuration.execute(
                Statement.CONFIGURATION_WRITE_CONFIGURATION_ACTIVE_VERSIONS_013,
                (
                    current["contractId"],
                    version_id,
                    actor.user_id,
                    None,
                    current["rollbackTargetId"],
                ),
            )
            _append_lifecycle(
                connection,
                actor,
                version_id=version_id,
                contract_id=current["contractId"],
                version=current["version"],
                state="active",
                action="activate",
                rationale=rationale,
                test_evidence_id=current["testEvidenceId"],
                approval_id=current["approvalId"],
                rollback_target_id=current["rollbackTargetId"],
            )
            connection.commit()
        return {**current, "state": "active"}

    return execute_authorized(
        actor,
        Action.ACTIVATE,
        configuration_scope(actor, version["contractId"]),
        command,
    )


def supersede_version(
    actor: Actor,
    active_version_id: str,
    successor_version_id: str,
    rationale: str,
) -> dict:
    rationale = _rationale(rationale)
    with database() as connection:
        active_version = _details(connection, active_version_id)

    def command():
        with database() as connection:
            predecessor = _details(connection, active_version_id)
            successor = _details(connection, successor_version_id)
            if predecessor["contractId"] != successor["contractId"]:
                raise InvalidConfiguration("Successor must belong to the same contract")
            if predecessor["state"] != "active" or successor["state"] != "approved":
                raise InvalidConfiguration("Supersession requires active predecessor and approved successor")
            active = connection.configuration.execute(
                Statement.CONFIGURATION_READ_CONFIGURATION_ACTIVE_VERSIONS_012,
                (predecessor["contractId"],),
            ).fetchone()
            if not active or active[0] != active_version_id:
                raise InvalidConfiguration("The predecessor is not the current active version")
            cursor = connection.configuration.execute(
                Statement.CONFIGURATION_WRITE_CONFIGURATION_ACTIVE_VERSIONS_016,
                (
                    successor_version_id,
                    actor.user_id,
                    active_version_id,
                    successor["rollbackTargetId"],
                    predecessor["contractId"],
                    active_version_id,
                ),
            )
            if cursor.rowcount != 1:
                raise InvalidConfiguration("Supersession was stale")
            _append_lifecycle(
                connection,
                actor,
                version_id=active_version_id,
                contract_id=predecessor["contractId"],
                version=predecessor["version"],
                state="superseded",
                action="supersede",
                rationale=rationale,
                test_evidence_id=predecessor["testEvidenceId"],
                approval_id=predecessor["approvalId"],
                successor_id=successor_version_id,
            )
            _append_lifecycle(
                connection,
                actor,
                version_id=successor_version_id,
                contract_id=successor["contractId"],
                version=successor["version"],
                state="active",
                action="activate",
                rationale=rationale,
                test_evidence_id=successor["testEvidenceId"],
                approval_id=successor["approvalId"],
                predecessor_id=active_version_id,
                rollback_target_id=successor["rollbackTargetId"],
            )
            connection.commit()
        return {
            "predecessorId": active_version_id,
            "successorId": successor_version_id,
            "state": "active",
        }

    return execute_authorized(
        actor,
        Action.SUPERSEDE,
        configuration_scope(actor, active_version["contractId"]),
        command,
    )


def retire_version(actor: Actor, version_id: str, rationale: str) -> dict:
    rationale = _rationale(rationale)
    with database() as connection:
        version = _details(connection, version_id)

    def command():
        with database() as connection:
            current = _details(connection, version_id)
            if current["state"] != "superseded":
                raise InvalidConfiguration("Only a superseded version may be retired")
            _append_lifecycle(
                connection,
                actor,
                version_id=version_id,
                contract_id=current["contractId"],
                version=current["version"],
                state="retired",
                action="retire",
                rationale=rationale,
                test_evidence_id=current["testEvidenceId"],
                approval_id=current["approvalId"],
            )
            connection.commit()
        return {**current, "state": "retired"}

    return execute_authorized(
        actor,
        Action.RETIRE,
        configuration_scope(actor, version["contractId"]),
        command,
    )


def rollback_version(
    actor: Actor,
    contract_id: str,
    target_version_id: str,
    rationale: str,
) -> dict:
    rationale = _rationale(rationale)

    def command():
        with database() as connection:
            target = _details(connection, target_version_id)
            if target["contractId"] != contract_id:
                raise InvalidConfiguration("Rollback target belongs to another contract")
            if target["state"] not in {"superseded", "retired"}:
                raise InvalidConfiguration("Rollback target must be superseded or retired")
            result = _create_tested_version(
                connection,
                actor,
                contract_id,
                target["configuration"],
                rationale,
                action="rollback",
                rollback_target_id=target_version_id,
            )
            connection.commit()
        return result

    return execute_authorized(
        actor,
        Action.ROLLBACK,
        configuration_scope(actor, contract_id),
        command,
    )


def get_draft(actor: Actor, contract_id: str) -> dict:
    require_permission(actor, Action.READ, configuration_scope(actor, contract_id))
    with database() as connection:
        row = connection.configuration.execute(
            Statement.CONFIGURATION_READ_CONFIGURATION_DRAFTS_002,
            (contract_id,),
        ).fetchone()
    if not row:
        raise InvalidConfiguration("No draft exists")
    return row[0]


def lifecycle_history(actor: Actor, contract_id: str) -> dict:
    require_permission(actor, Action.READ, configuration_scope(actor, contract_id))
    with database() as connection:
        rows = connection.configuration.execute(
            Statement.CONFIGURATION_READ_CONFIGURATION_ACTIVE_VERSIONS_CONFIGURATION_LIFECYCLE_EVENTS_CONFIGURATION_VERSIONS_014,
            (contract_id,),
        ).fetchall()
    versions: dict[str, dict] = {}
    for row in rows:
        version = versions.setdefault(
            row[0],
            {
                "id": row[0],
                "version": row[1],
                "configuration": row[2],
                "state": row[3],
                "active": row[16],
                "history": [],
            },
        )
        version["state"] = row[3]
        version["active"] = row[16]
        version["history"].append(
            {
                "state": row[3],
                "action": row[4],
                "actorId": row[5],
                "actorRole": row[6],
                "actorOrganizationId": row[7],
                "rationale": row[8],
                "testEvidenceId": row[9],
                "approvalId": row[10],
                "predecessorVersionId": row[11],
                "successorVersionId": row[12],
                "rollbackTargetVersionId": row[13],
                "eventHash": row[14],
                "occurredAt": row[15].isoformat(),
            }
        )
    return ConfigurationLifecycleResponseDto.model_validate(
        {"versions": list(versions.values())}
    ).model_dump(by_alias=True, mode="json")


def active_summary(actor: Actor, contract_id: str) -> dict | None:
    require_permission(
        actor,
        Action.READ,
        configuration_scope(actor, contract_id, active_only=True),
    )
    with database() as connection:
        row = connection.configuration.execute(
            Statement.CONFIGURATION_READ_CONFIGURATION_VERSIONS_006,
            (contract_id,),
        ).fetchone()
    return (
        ActiveConfigurationDto(
            id=row[0],
            version=row[1],
            activated_at=row[2].isoformat(),
        ).model_dump(by_alias=True)
        if row
        else None
    )
