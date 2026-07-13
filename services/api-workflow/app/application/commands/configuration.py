from copy import deepcopy
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
import uuid

from .access_scope import configuration_scope
from .document_profiles import InvalidDocumentProfile, activate_profile_references_tx
from ...authorization import Action, Actor, execute_authorized, require_permission
from .provenance import append_event_tx
from ...shared_contracts import (
    ActiveConfigurationDto,
    ConfigurationActivationImpactDto,
    ConfigurationDiffDto,
    ConfigurationDraftDto,
    ConfigurationLifecycleResponseDto,
    ConfigurationReferencesDto,
)

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


def _configuration_payload(value: dict) -> dict:
    snapshot = deepcopy(value)
    for field in ("id", "version", "status"):
        snapshot.pop(field, None)
    return snapshot


def _draft_projection(row: tuple) -> dict:
    return ConfigurationDraftDto(
        configuration=row[0],
        revision=row[1],
        payload_hash=_hash(_configuration_payload(row[0])),
        updated_at=row[2],
    ).model_dump(by_alias=True, mode="json")


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
    profile_references = payload.get("documentProfiles")
    if (
        not isinstance(profile_references, list)
        or not profile_references
        or any(
            not isinstance(reference, dict)
            or reference.get("kind") != "document_profile"
            or not isinstance(reference.get("id"), str)
            or not reference["id"].strip()
            or isinstance(reference.get("version"), bool)
            or not isinstance(reference.get("version"), int)
            or reference["version"] < 1
            or not isinstance(reference.get("sha256"), str)
            or not re.fullmatch(r"[a-f0-9]{64}", reference["sha256"])
            for reference in profile_references
        )
        or len({reference["id"] for reference in profile_references})
        != len(profile_references)
    ):
        raise InvalidConfiguration(
            "Exact document profile id, version, and hash references are required"
        )


def _test_report(payload: dict) -> dict:
    validate_configuration(payload)
    checks = [
        {"code": "SERVICE_PERIOD", "passed": True},
        {"code": "CATEGORY_SCHEMA", "passed": True},
        {"code": "EVIDENCE_REQUIREMENTS", "passed": True},
        {"code": "DETERMINISTIC_RULE_SET", "passed": True},
        {"code": "WORKFLOW_AND_TEMPLATE", "passed": True},
        {"code": "DOCUMENT_PROFILE_REFERENCES", "passed": True},
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
        "testResults": row[8],
        "testedBy": row[9],
        "testedRole": row[10],
        "testedOrganizationId": row[11],
        "testRationale": row[12],
        "testedAt": row[13],
        "approvalId": row[14],
        "approvalTestEvidenceId": row[15],
        "approvedBy": row[16],
        "approvedRole": row[17],
        "approvedOrganizationId": row[18],
        "approvalRationale": row[19],
        "approvalHash": row[20],
        "approvedAt": row[21],
        "rollbackTargetId": row[22],
        "active": row[23],
    }


def _test_evidence(details: dict) -> dict | None:
    if not details["testEvidenceId"]:
        return None
    results = details["testResults"] or {}
    return {
        "id": details["testEvidenceId"],
        "suiteVersion": details["testSuiteVersion"],
        "payloadHash": details["payloadHash"],
        "resultHash": details["testResultHash"],
        "passed": results.get("passed") is True,
        "checks": results.get("checks", []),
        "testedBy": details["testedBy"],
        "testedRole": details["testedRole"],
        "testedOrganizationId": details["testedOrganizationId"],
        "rationale": details["testRationale"],
        "createdAt": details["testedAt"],
    }


def _approval_evidence(details: dict) -> dict | None:
    if not details["approvalId"]:
        return None
    return {
        "id": details["approvalId"],
        "testEvidenceId": details["approvalTestEvidenceId"],
        "approvedBy": details["approvedBy"],
        "approvedRole": details["approvedRole"],
        "approvedOrganizationId": details["approvedOrganizationId"],
        "rationale": details["approvalRationale"],
        "approvalHash": details["approvalHash"],
        "approvedAt": details["approvedAt"],
    }


def _require_current_successful_evidence(details: dict, *, require_approval: bool) -> None:
    payload = _configuration_payload(details["configuration"])
    expected_payload_hash = _hash(payload)
    expected_report = _test_report(payload)
    expected_result_hash = _hash(
        {"payloadHash": expected_payload_hash, "report": expected_report}
    )
    if (
        not details["testEvidenceId"]
        or details["testSuiteVersion"] != TEST_SUITE_VERSION
        or details["testResults"] != expected_report
        or details["payloadHash"] != expected_payload_hash
        or details["testResultHash"] != expected_result_hash
        or details["testResults"].get("passed") is not True
    ):
        raise InvalidConfiguration(
            "Current successful deterministic test evidence is required"
        )
    if not require_approval:
        return
    approval_body = {
        "id": details["approvalId"],
        "configurationVersionId": details["id"],
        "testEvidenceId": details["approvalTestEvidenceId"],
        "approvedBy": details["approvedBy"],
        "approvedRole": details["approvedRole"],
        "approvedOrganizationId": details["approvedOrganizationId"],
        "rationale": details["approvalRationale"],
    }
    if (
        not details["approvalId"]
        or details["approvalTestEvidenceId"] != details["testEvidenceId"]
        or details["approvalHash"] != _hash(approval_body)
    ):
        raise InvalidConfiguration(
            "Approval must be bound to the current immutable test evidence"
        )


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
    snapshot = _configuration_payload(payload)
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


def update_draft(
    actor: Actor,
    contract_id: str,
    payload: dict,
    expected_revision: int | None = None,
) -> dict:
    validate_configuration(payload)
    snapshot = deepcopy(payload)
    snapshot["status"] = "draft"

    def command():
        with database() as connection:
            resolved_revision = expected_revision
            current = connection.configuration.execute(
                Statement.CONFIGURATION_READ_CONFIGURATION_DRAFTS_017,
                (contract_id,),
            ).fetchone()
            if resolved_revision is None:
                resolved_revision = current[1] if current else 0
            if resolved_revision < 0:
                raise InvalidConfiguration("Expected draft revision cannot be negative")
            if (current and current[1] != resolved_revision) or (
                not current and resolved_revision != 0
            ):
                raise InvalidConfiguration("Configuration draft revision is stale")
            row = connection.configuration.execute(
                Statement.CONFIGURATION_WRITE_CONFIGURATION_DRAFTS_001,
                (
                    contract_id,
                    json.dumps(snapshot),
                    actor.user_id,
                    resolved_revision,
                ),
            ).fetchone()
            if not row:
                raise InvalidConfiguration("Configuration draft revision is stale")
            connection.commit()
        return _draft_projection(row)

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


def test_draft(
    actor: Actor,
    contract_id: str,
    rationale: str,
    expected_revision: int | None = None,
) -> dict:
    rationale = _rationale(rationale)

    def command():
        with database() as connection:
            row = connection.configuration.execute(
                Statement.CONFIGURATION_READ_CONFIGURATION_DRAFTS_017,
                (contract_id,),
            ).fetchone()
            if not row:
                raise InvalidConfiguration("No draft exists")
            if expected_revision is not None and row[1] != expected_revision:
                raise InvalidConfiguration("Configuration draft revision is stale")
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
            _require_current_successful_evidence(current, require_approval=False)
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
            _require_current_successful_evidence(current, require_approval=True)
            active = connection.configuration.execute(
                Statement.CONFIGURATION_READ_CONFIGURATION_ACTIVE_VERSIONS_012,
                (current["contractId"],),
            ).fetchone()
            if active:
                raise InvalidConfiguration(
                    "Supersede the current active version with this approved successor"
                )
            try:
                activate_profile_references_tx(
                    connection,
                    actor,
                    current["contractId"],
                    version_id,
                    current["configuration"]["documentProfiles"],
                    rationale,
                )
            except InvalidDocumentProfile as error:
                raise InvalidConfiguration(str(error)) from error
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
            _require_current_successful_evidence(successor, require_approval=True)
            active = connection.configuration.execute(
                Statement.CONFIGURATION_READ_CONFIGURATION_ACTIVE_VERSIONS_012,
                (predecessor["contractId"],),
            ).fetchone()
            if not active or active[0] != active_version_id:
                raise InvalidConfiguration("The predecessor is not the current active version")
            try:
                activate_profile_references_tx(
                    connection,
                    actor,
                    successor["contractId"],
                    successor_version_id,
                    successor["configuration"]["documentProfiles"],
                    rationale,
                    activation_action=(
                        "rollback" if successor["rollbackTargetId"] else "activate"
                    ),
                )
            except InvalidDocumentProfile as error:
                raise InvalidConfiguration(str(error)) from error
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
    return get_draft_details(actor, contract_id)["configuration"]


def get_draft_details(actor: Actor, contract_id: str) -> dict:
    require_permission(actor, Action.READ, configuration_scope(actor, contract_id))
    with database() as connection:
        row = connection.configuration.execute(
            Statement.CONFIGURATION_READ_CONFIGURATION_DRAFTS_002,
            (contract_id,),
        ).fetchone()
    if not row:
        raise InvalidConfiguration("No draft exists")
    return _draft_projection(row)


def lifecycle_history(actor: Actor, contract_id: str) -> dict:
    require_permission(actor, Action.READ, configuration_scope(actor, contract_id))
    with database() as connection:
        rows = connection.configuration.execute(
            Statement.CONFIGURATION_READ_CONFIGURATION_ACTIVE_VERSIONS_CONFIGURATION_LIFECYCLE_EVENTS_CONFIGURATION_VERSIONS_014,
            (contract_id,),
        ).fetchall()
        version_ids = dict.fromkeys(row[0] for row in rows)
        details = {
            version_id: _details(connection, version_id)
            for version_id in version_ids
        }
    versions: dict[str, dict] = {}
    for row in rows:
        detail = details[row[0]]
        version = versions.setdefault(
            row[0],
            {
                "id": row[0],
                "contractId": detail["contractId"],
                "version": row[1],
                "configuration": row[2],
                "state": row[3],
                "active": row[16],
                "payloadHash": detail["payloadHash"],
                "testEvidence": _test_evidence(detail),
                "approval": _approval_evidence(detail),
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


def configuration_version_detail(actor: Actor, version_id: str) -> dict:
    with database() as connection:
        details = _details(connection, version_id)
    require_permission(
        actor,
        Action.READ,
        configuration_scope(actor, details["contractId"]),
    )
    versions = lifecycle_history(actor, details["contractId"])["versions"]
    return next(version for version in versions if version["id"] == version_id)


def _flatten(value: object, path: str = "") -> dict[str, object]:
    if isinstance(value, dict):
        if not value:
            return {path or "/": {}}
        flattened: dict[str, object] = {}
        for key in sorted(value):
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            flattened.update(_flatten(value[key], f"{path}/{escaped}"))
        return flattened
    if isinstance(value, list):
        if not value:
            return {path or "/": []}
        flattened = {}
        for index, item in enumerate(value):
            flattened.update(_flatten(item, f"{path}/{index}"))
        return flattened
    return {path or "/": value}


def _display(value: object) -> str:
    rendered = _canonical(value)
    return rendered if len(rendered) <= 120 else rendered[:117] + "..."


def compare_configuration_versions(
    actor: Actor,
    base_version_id: str,
    target_version_id: str,
) -> dict:
    with database() as connection:
        base = _details(connection, base_version_id)
        target = _details(connection, target_version_id)
    require_permission(
        actor,
        Action.READ,
        configuration_scope(actor, base["contractId"]),
    )
    require_permission(
        actor,
        Action.READ,
        configuration_scope(actor, target["contractId"]),
    )
    if base["contractId"] != target["contractId"]:
        raise InvalidConfiguration("Compared versions must belong to the same contract")
    before = _flatten(_configuration_payload(base["configuration"]))
    after = _flatten(_configuration_payload(target["configuration"]))
    changes = []
    for path in sorted(set(before) | set(after)):
        if path not in before:
            change_type = "added"
            description = f"{path} added as {_display(after[path])}"
        elif path not in after:
            change_type = "removed"
            description = f"{path} removed (was {_display(before[path])})"
        elif before[path] != after[path]:
            change_type = "changed"
            description = (
                f"{path} changed from {_display(before[path])} "
                f"to {_display(after[path])}"
            )
        else:
            continue
        changes.append(
            {
                "path": path,
                "changeType": change_type,
                "before": before.get(path),
                "after": after.get(path),
                "description": description,
            }
        )
    projection = {
        "contractId": base["contractId"],
        "baseVersionId": base_version_id,
        "targetVersionId": target_version_id,
        "changes": changes,
        "canonical": False,
    }
    projection["projectionHash"] = _hash(projection)
    return ConfigurationDiffDto.model_validate(projection).model_dump(
        by_alias=True, mode="json"
    )


def configuration_references(actor: Actor, version_id: str) -> dict:
    with database() as connection:
        details = _details(connection, version_id)
    require_permission(
        actor,
        Action.READ,
        configuration_scope(actor, details["contractId"]),
    )
    with database() as connection:
        rows = connection.read_models.execute(
            Statement.CONFIGURATION_READ_DOMAIN_EVENTS_INVOICE_SNAPSHOTS_INVOICE_VERSIONS_PACKAGES_SUBMISSIONS_VALIDATION_RUNS_018,
            (version_id,) * 6,
        ).fetchall()
    references = [
        {
            "resourceKind": row[0],
            "resourceId": row[1],
            "resourceVersion": row[2],
            "state": row[3],
            "recordedAt": row[4].isoformat().replace("+00:00", "Z"),
        }
        for row in rows
    ]
    projection = {
        "configurationVersionId": version_id,
        "references": references,
        "canonical": False,
    }
    projection["projectionHash"] = _hash(projection)
    return ConfigurationReferencesDto.model_validate(projection).model_dump(
        by_alias=True, mode="json"
    )


def configuration_activation_impact(actor: Actor, version_id: str) -> dict:
    with database() as connection:
        details = _details(connection, version_id)
        active = connection.configuration.execute(
            Statement.CONFIGURATION_READ_CONFIGURATION_VERSIONS_006,
            (details["contractId"],),
        ).fetchone()
    require_permission(
        actor,
        Action.READ,
        configuration_scope(actor, details["contractId"]),
    )
    historical_version_id = (
        active[0] if active and active[0] != version_id else None
    )
    references = (
        configuration_references(actor, historical_version_id)["references"]
        if historical_version_id
        else []
    )
    counts = dict(sorted(Counter(item["resourceKind"] for item in references).items()))
    projection = {
        "configurationVersionId": version_id,
        "contractId": details["contractId"],
        "wouldSupersedeVersionId": historical_version_id,
        "historicalReferenceVersionId": historical_version_id,
        "referenceCounts": counts,
        "applicationScope": "future-intake-only",
        "historicalReferencesPreserved": True,
        "canonical": False,
    }
    projection["projectionHash"] = _hash(projection)
    return ConfigurationActivationImpactDto.model_validate(projection).model_dump(
        by_alias=True, mode="json"
    )


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
