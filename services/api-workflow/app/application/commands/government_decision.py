import json
import uuid

from ...authorization import Action, Actor, execute_authorized
from .access_scope import government_decision_scope
from .provenance import append_event_tx, append_relation_tx
from .revision import create_return_revision_tx

from ..ports.statements import Statement
from ..transaction import transaction as database


RETURN_REASONS = {"EVIDENCE_CORRECTION", "AMOUNT_CORRECTION", "CLARIFICATION"}
APPROVAL_REASONS = {"APPROVED_AS_CORRECTED"}


class DecisionError(ValueError):
    pass


def _validated_decision_input(
    decision: str,
    reason_code: str,
    note: str,
    line_keys: list[str],
    exact_invoice_line_keys: set[str],
) -> tuple[str, list[str]]:
    normalized_note = note.strip()
    normalized_lines = [line.strip() for line in line_keys]
    if not normalized_note:
        raise DecisionError("A decision note is required")
    if any(not line for line in normalized_lines):
        raise DecisionError("Affected expense keys cannot be blank")
    if len(normalized_lines) != len(set(normalized_lines)):
        raise DecisionError("Affected expense keys must be unique")
    if decision == "returned":
        if reason_code not in RETURN_REASONS:
            raise DecisionError("A supported return reason is required")
        if not normalized_lines:
            raise DecisionError("A return must identify at least one affected expense")
        unknown = sorted(set(normalized_lines) - exact_invoice_line_keys)
        if unknown:
            raise DecisionError(
                "Affected expenses do not belong to the exact submitted invoice: "
                + ", ".join(unknown)
            )
    elif decision == "approved":
        if reason_code not in APPROVAL_REASONS:
            raise DecisionError("A supported approval reason is required")
        if normalized_lines:
            raise DecisionError("Final approval cannot introduce affected expense keys")
    else:
        raise DecisionError("Unsupported decision")
    return normalized_note, normalized_lines


def decide(
    actor: Actor,
    queue_id: str,
    decision: str,
    reason_code: str,
    note: str,
    line_keys: list[str],
) -> dict:
    if decision not in {"returned", "approved"}:
        raise DecisionError("Unsupported decision")
    with database() as connection:
        row = connection.read_models.execute(
            Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_QUEUE_ITEMS_INVOICE_VERSIONS_SUBMISSIONS_001,
            (queue_id,),
        ).fetchone()
    if not row:
        raise FileNotFoundError(queue_id)
    scope = government_decision_scope(actor, queue_id)
    action = Action.RETURN if decision == "returned" else Action.APPROVE

    def command() -> dict:
        with database() as connection:
            human = connection.identity.execute(
                Statement.GOVERNMENT_DECISION_READ_USERS_002,
                (actor.user_id,),
            ).fetchone()
            if human != (actor.role.value, actor.organization_id):
                raise DecisionError("Decision actor must be a provisioned human reviewer")
            current_row = connection.workflow.execute(
                Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_QUEUE_ITEMS_003,
                (queue_id,),
            ).fetchone()
            if not current_row or current_row[0] != "submitted":
                raise DecisionError("Decision is stale or out of order")
            exact_line_keys = {
                item[0]
                for item in connection.invoices.execute(
                    Statement.GOVERNMENT_DECISION_READ_INVOICE_LINES_009,
                    (row[4],),
                ).fetchall()
            }
            normalized_note, normalized_lines = _validated_decision_input(
                decision,
                reason_code,
                note,
                line_keys,
                exact_line_keys,
            )
            if decision == "returned" and connection.read_models.execute(
                Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_DECISIONS_INVOICE_VERSIONS_SUBMISSIONS_004,
                (row[7],),
            ).fetchone():
                raise DecisionError("The canonical return has already occurred")
            if decision == "approved":
                prior = connection.read_models.execute(
                    Statement.GOVERNMENT_DECISION_READ_GOVERNMENT_DECISIONS_INVOICE_VERSIONS_SUBMISSIONS_005,
                    (row[7], row[6]),
                ).fetchone()
                if row[6] < 2 or not prior:
                    raise DecisionError("Approval requires a corrected resubmission after return")

            decision_id = f"decision-{uuid.uuid4().hex}"
            connection.workflow.execute(
                Statement.GOVERNMENT_DECISION_WRITE_GOVERNMENT_DECISIONS_006,
                (
                    decision_id,
                    queue_id,
                    row[3],
                    row[4],
                    row[5],
                    decision,
                    reason_code,
                    normalized_note,
                    json.dumps(normalized_lines),
                    actor.user_id,
                    actor.role.value,
                ),
            )
            connection.workflow.execute(
                Statement.GOVERNMENT_DECISION_WRITE_GOVERNMENT_QUEUE_ITEMS_007,
                (decision, queue_id),
            )
            connection.invoices.execute(
                Statement.GOVERNMENT_DECISION_WRITE_INVOICE_VERSIONS_008,
                (decision, row[4]),
            )
            successor = None
            if decision == "returned":
                successor = create_return_revision_tx(
                    connection,
                    row[4],
                    decision_id,
                    actor.user_id,
                    row[2],
                    row[7],
                    actor.organization_id,
                )
            if decision == "approved":
                append_relation_tx(
                    connection,
                    row[7],
                    row[2],
                    "approved_as",
                    {"kind": "submission", "id": row[3], "version": row[6]},
                    {"kind": "decision", "id": decision_id, "version": 1},
                    actor=actor,
                    reason_code=reason_code,
                )
            append_event_tx(
                connection,
                decision,
                "invoice_version",
                row[4],
                actor_id=actor.user_id,
                organization_id=row[2],
                contract_id=row[7],
                payload={
                    "decisionId": decision_id,
                    "queueItemId": queue_id,
                    "submissionId": row[3],
                    "packageId": row[5],
                    "invoiceVersion": row[6],
                    "reasonCode": reason_code,
                    "note": normalized_note,
                    "lineKeys": normalized_lines,
                },
                reason_code=reason_code,
                version_references=[
                    {"kind": "invoice", "id": row[4], "version": row[6]},
                    {"kind": "submission", "id": row[3], "version": row[6]},
                    {"kind": "package", "id": row[5], "version": row[6]},
                    {"kind": "decision", "id": decision_id, "version": 1},
                ],
            )
            connection.commit()
        return {
            "id": decision_id,
            "queueItemId": queue_id,
            "submissionId": row[3],
            "invoiceVersionId": row[4],
            "successorInvoiceVersionId": successor,
            "packageId": row[5],
            "invoiceVersion": row[6],
            "decision": decision,
            "reasonCode": reason_code,
            "note": normalized_note,
            "lineKeys": normalized_lines,
            "actorId": actor.user_id,
            "actorRole": actor.role.value,
        }

    return execute_authorized(actor, action, scope, command)
