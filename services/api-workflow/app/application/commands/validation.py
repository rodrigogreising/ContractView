from __future__ import annotations

from datetime import date
from decimal import Decimal
import json
import uuid

from .access_scope import invoice_scope
from .budget import calculate_budget
from .invoice_snapshots import create_invoice_snapshot_tx
from .provenance import append_event_tx, append_relation_tx
from ..ports.statements import Statement
from ..reproducibility import (
    canonical_document,
    canonical_hash,
    validation_input_manifest,
)
from ..transaction import transaction as database
from ...authorization import Action, Actor, execute_authorized, require_permission
from ...shared_contracts import (
    RuleDefinition,
    RuleResult,
    ValidationInputManifestContract,
    ValidationRunDto,
)


ENGINE_VERSION = "deterministic-validation-v2"


def _result(
    rule: RuleDefinition,
    reason: str,
    outcome: str,
    message: str,
    normalized: dict,
    expense: str | None = None,
) -> dict:
    return RuleResult(
        rule_code=rule.code,
        rule_version=rule.version,
        severity=rule.severity,
        reason_code=reason,
        outcome=outcome,
        expense_key=expense,
        normalized_input=normalized,
        message=message,
    ).model_dump(by_alias=True, mode="json")


def execute_rule_contracts(manifest: ValidationInputManifestContract) -> list[dict]:
    """Execute only validated, versioned shared rule contracts."""

    normalized = manifest.normalized_inputs
    lines = normalized["lines"]
    rules = {rule.code.value: rule for rule in manifest.rules if rule.enabled}
    results: list[dict] = []

    if rule := rules.get("SERVICE_PERIOD"):
        period = rule.parameters["servicePeriod"]
        start = date.fromisoformat(period["start"])
        end = date.fromisoformat(period["end"])
        for row in lines:
            expense_date = date.fromisoformat(row["date"])
            passed = start <= expense_date <= end
            results.append(
                _result(
                    rule,
                    "IN_SERVICE_PERIOD" if passed else f"SERVICE_PERIOD:{row['expenseKey']}",
                    "pass" if passed else "fail",
                    (
                        f"{expense_date} is within {start}..{end}"
                        if passed
                        else f"{expense_date} is outside {start}..{end}"
                    ),
                    {
                        "date": expense_date.isoformat(),
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                    },
                    row["expenseKey"],
                )
            )

    if rule := rules.get("REQUIRED_EVIDENCE"):
        for row in lines:
            passed = row["evidenceArtifactId"] is not None
            results.append(
                _result(
                    rule,
                    (
                        "EVIDENCE_PRESENT"
                        if passed
                        else f"REQUIRED_EVIDENCE:{row['expenseKey']}"
                    ),
                    "pass" if passed else "fail",
                    "Supporting evidence is linked" if passed else "Supporting evidence is missing",
                    {"evidenceArtifactId": row["evidenceArtifactId"]},
                    row["expenseKey"],
                )
            )

    category_totals: dict[str, Decimal] = {}
    for row in lines:
        category_totals[row["category"]] = category_totals.get(
            row["category"], Decimal("0.00")
        ) + Decimal(row["amount"])

    if rule := rules.get("BUDGET_AVAILABLE"):
        budget = calculate_budget(category_totals, rule.parameters["categories"])
        for category in budget["categories"]:
            passed = not category["overBudget"]
            results.append(
                _result(
                    rule,
                    (
                        "BUDGET_AVAILABLE"
                        if passed
                        else f"BUDGET_AVAILABLE:{category['code']}"
                    ),
                    "pass" if passed else "fail",
                    (
                        f"Requested {category['requested']:.2f}; "
                        f"limit {category['budgeted']:.2f}"
                    ),
                    {
                        "category": category["name"],
                        "requested": f"{category['requested']:.2f}",
                        "limit": f"{category['budgeted']:.2f}",
                        "remaining": f"{category['remaining']:.2f}",
                    },
                )
            )

    if rule := rules.get("TOTAL_RECONCILIATION"):
        calculated = sum((Decimal(row["amount"]) for row in lines), Decimal("0.00"))
        invoice_total = Decimal(normalized["total"])
        control = Decimal(str(rule.parameters["ledgerControlTotal"]))
        passed = calculated == invoice_total == control
        results.append(
            _result(
                rule,
                "TOTAL_RECONCILED" if passed else "TOTAL_RECONCILIATION",
                "pass" if passed else "fail",
                (
                    f"Invoice {invoice_total:.2f}; lines {calculated:.2f}; "
                    f"control {control:.2f}"
                ),
                {
                    "invoiceTotal": f"{invoice_total:.2f}",
                    "lineTotal": f"{calculated:.2f}",
                    "controlTotal": f"{control:.2f}",
                },
            )
        )

    if rule := rules.get("POSSIBLE_DUPLICATE"):
        window = int(rule.parameters["dayWindow"])
        tolerance = Decimal(str(rule.parameters["amountTolerance"]))
        duplicates = []
        for index, left in enumerate(lines):
            for right in lines[index + 1 :]:
                amount_difference = abs(Decimal(left["amount"]) - Decimal(right["amount"]))
                day_difference = abs(
                    (date.fromisoformat(left["date"]) - date.fromisoformat(right["date"])).days
                )
                if (
                    left["vendor"] == right["vendor"]
                    and amount_difference <= tolerance
                    and day_difference <= window
                ):
                    duplicates.append((left, right, amount_difference, day_difference))
        if duplicates:
            for left, right, amount_difference, day_difference in duplicates:
                results.append(
                    _result(
                        rule,
                        f"POSSIBLE_DUPLICATE:{right['expenseKey']}:{left['expenseKey']}",
                        "fail",
                        f"{right['expenseKey']} may duplicate {left['expenseKey']}",
                        {
                            "left": left["expenseKey"],
                            "right": right["expenseKey"],
                            "vendor": left["vendor"],
                            "amountDifference": f"{amount_difference:.2f}",
                            "dayDifference": day_difference,
                            "tolerance": f"{tolerance:.2f}",
                            "window": window,
                        },
                        right["expenseKey"],
                    )
                )
        else:
            results.append(
                _result(
                    rule,
                    "NO_POSSIBLE_DUPLICATE",
                    "pass",
                    "No configured duplicate candidate",
                    {"tolerance": f"{tolerance:.2f}", "window": window},
                )
            )

    return sorted(
        results,
        key=lambda item: (item["ruleCode"], item["expenseKey"] or "", item["reasonCode"]),
    )


def execute_validation(actor: Actor, invoice_id: str) -> dict:
    def command():
        with database() as connection:
            invoice = connection.invoices.execute(
                Statement.VALIDATION_READ_INVOICE_VERSIONS_001, (invoice_id,)
            ).fetchone()
            if not invoice:
                raise FileNotFoundError(invoice_id)
            config_row = connection.configuration.execute(
                Statement.VALIDATION_READ_CONFIGURATION_VERSIONS_002, (invoice[1],)
            ).fetchone()
            if not config_row:
                raise RuntimeError("Invoice configuration version is missing")
            configuration = config_row[0]
            snapshot = create_invoice_snapshot_tx(connection, actor, invoice_id, "validation")
            extraction_rows = connection.read_models.execute(
                Statement.VALIDATION_READ_ARTIFACTS_EXTRACTION_FIELDS_EXTRACTION_RUNS_INVOICE_LINES_003,
                (invoice_id,),
            ).fetchall()
            manifest_model = validation_input_manifest(
                snapshot, configuration, extraction_rows, ENGINE_VERSION
            )
            manifest = canonical_document(manifest_model)
            input_hash = canonical_hash(manifest)
            manifest_id = f"validation-input-{input_hash}"
            stable_results = execute_rule_contracts(manifest_model)
            output_hash = canonical_hash(stable_results)
            run_id = f"validation-{uuid.uuid4().hex}"
            connection.validation.execute(
                Statement.VALIDATION_WRITE_VALIDATION_INPUT_MANIFESTS_011,
                (
                    manifest_id,
                    snapshot["id"],
                    manifest_model.schema_version,
                    json.dumps(manifest),
                    input_hash,
                ),
            )
            connection.validation.execute(
                Statement.VALIDATION_WRITE_VALIDATION_RUNS_004,
                (
                    run_id,
                    invoice_id,
                    invoice[1],
                    ENGINE_VERSION,
                    json.dumps(manifest_model.normalized_inputs),
                    input_hash,
                    output_hash,
                    actor.user_id,
                    invoice[4],
                    snapshot["id"],
                    manifest_id,
                ),
            )
            append_relation_tx(
                connection,
                invoice[0],
                invoice[2],
                "validated_by",
                {
                    "kind": "invoice_snapshot",
                    "id": snapshot["id"],
                    "version": invoice[4],
                    "sha256": snapshot["sha256"],
                },
                {"kind": "validation_run", "id": run_id, "version": ENGINE_VERSION},
                actor=actor,
            )
            for item in stable_results:
                result_id = f"result-{uuid.uuid4().hex}"
                connection.validation.execute(
                    Statement.VALIDATION_WRITE_VALIDATION_RESULTS_005,
                    (
                        result_id,
                        run_id,
                        item["ruleCode"],
                        item["ruleVersion"],
                        item["severity"],
                        item["reasonCode"],
                        item["outcome"],
                        item["expenseKey"],
                        json.dumps(item["normalizedInput"]),
                        item["message"],
                    ),
                )
                if item["outcome"] == "fail":
                    connection.validation.execute(
                        Statement.VALIDATION_WRITE_VALIDATION_FINDINGS_006,
                        (
                            f"validation-finding-{uuid.uuid4().hex}",
                            result_id,
                            invoice_id,
                            run_id,
                            item["expenseKey"],
                            item["reasonCode"],
                            item["severity"],
                            item["message"],
                        ),
                    )
            append_event_tx(
                connection,
                "validation_completed",
                "validation_run",
                run_id,
                actor_id=actor.user_id,
                organization_id=invoice[2],
                contract_id=invoice[0],
                payload={
                    "invoiceVersionId": invoice_id,
                    "configurationVersionId": invoice[1],
                    "engineVersion": ENGINE_VERSION,
                    "inputManifestId": manifest_id,
                    "inputHash": input_hash,
                    "outputHash": output_hash,
                    "invoiceSnapshotId": snapshot["id"],
                },
                version_references=[
                    {"kind": "validation_run", "id": run_id, "version": ENGINE_VERSION},
                    {
                        "kind": "invoice_snapshot",
                        "id": snapshot["id"],
                        "version": invoice[4],
                        "sha256": snapshot["sha256"],
                    },
                    {
                        "kind": "invoice",
                        "id": invoice_id,
                        "version": snapshot["payload"]["invoiceVersion"],
                    },
                    {"kind": "configuration", "id": invoice[1], "version": invoice[1]},
                ],
            )
            connection.commit()
        return get_validation(actor, run_id)

    return execute_authorized(actor, Action.CREATE, invoice_scope(actor, invoice_id), command)


def get_validation(actor: Actor, run_id: str) -> dict:
    with database() as connection:
        run = connection.validation.execute(
            Statement.VALIDATION_READ_VALIDATION_RUNS_007, (run_id,)
        ).fetchone()
        if not run:
            raise FileNotFoundError(run_id)
        require_permission(actor, Action.READ, invoice_scope(actor, run[1]))
        rows = connection.validation.execute(
            Statement.VALIDATION_READ_VALIDATION_RESULTS_008, (run_id,)
        ).fetchall()
    return ValidationRunDto(
        id=run[0],
        invoice_version_id=run[1],
        configuration_version_id=run[2],
        engine_version=run[3],
        normalized_inputs=run[4],
        input_hash=run[5],
        output_hash=run[6],
        status=run[7],
        input_manifest_id=run[8],
        input_manifest_hash=run[9],
        results=[
            {
                "ruleCode": row[0],
                "ruleVersion": row[1],
                "severity": row[2],
                "reasonCode": row[3],
                "outcome": row[4],
                "expenseKey": row[5],
                "normalizedInput": row[6],
                "message": row[7],
            }
            for row in rows
        ],
    ).model_dump(by_alias=True, mode="json")


def reproduce_validation(actor: Actor, run_id: str) -> dict:
    run = get_validation(actor, run_id)
    manifest_id = run.get("inputManifestId")
    if not manifest_id:
        raise ValueError("Validation run predates reproducibility manifests")
    with database() as connection:
        row = connection.validation.execute(
            Statement.VALIDATION_READ_VALIDATION_INPUT_MANIFESTS_010,
            (manifest_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("Validation input manifest is missing")
    manifest = ValidationInputManifestContract.model_validate(row[1])
    input_hash = canonical_hash(canonical_document(manifest))
    results = execute_rule_contracts(manifest)
    output_hash = canonical_hash(results)
    return {
        "validationRunId": run_id,
        "inputManifestId": row[0],
        "inputHash": input_hash,
        "outputHash": output_hash,
        "matches": input_hash == row[2] == run["inputHash"]
        and output_hash == run["outputHash"],
        "results": results,
    }


def latest_validation(actor: Actor, invoice_id: str) -> dict | None:
    with database() as connection:
        row = connection.validation.execute(
            Statement.VALIDATION_READ_VALIDATION_RUNS_009, (invoice_id,)
        ).fetchone()
    return get_validation(actor, row[0]) if row else None
