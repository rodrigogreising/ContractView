from dataclasses import dataclass
import uuid

from .access_scope import contract_scope, extraction_scope
from ...authorization import Action, Actor, ResourceKind, execute_authorized, require_permission
from .provenance import LineageInput, append_event_tx, append_lineage_tx


from ..ports.statements import Statement
from ..transaction import transaction as database
class InvalidReview(ValueError): pass
class UnreviewedField(ValueError): pass


def list_extractions(actor: Actor, contract_id: str) -> list[dict]:
    require_permission(
        actor,
        Action.READ,
        contract_scope(actor, contract_id, f"extractions:{contract_id}", ResourceKind.JOB),
    )
    with database() as connection:
        rows = connection.read_models.execute(Statement.EXTRACTION_REVIEW_READ_ARTIFACTS_EXTRACTION_FIELDS_EXTRACTION_RUNS_001, (contract_id,)
        ).fetchall()
    grouped: dict[str, dict] = {}
    for row in rows:
        require_permission(actor, Action.READ, extraction_scope(actor, row[0]))
        item = grouped.setdefault(row[0], {"id":row[0],"sourceArtifactId":row[1],"filename":row[2],"provider":row[3],"model":row[4],"status":row[5],"routingReason":row[6],"fields":[]})
        item["fields"].append({"id":row[7],"name":row[8],"proposedValue":row[9],"reviewedValue":row[10],"confidence":str(row[11]),"sourceLocation":row[12],"reviewStatus":row[13]})
    return list(grouped.values())


def review_field(actor: Actor, field_id: str, decision: str, value: str | None = None, reason: str | None = None) -> dict:
    if decision not in {"accept", "correct"}: raise InvalidReview("Decision must be accept or correct")

    def command() -> dict:
        with database() as connection:
            row = connection.extraction.execute(Statement.EXTRACTION_REVIEW_READ_EXTRACTION_FIELDS_EXTRACTION_RUNS_002, (field_id,)
            ).fetchone()
            if not row: raise FileNotFoundError(field_id)
            if row[1] != "proposed": raise InvalidReview("Field has already been reviewed")
            reviewed = row[0] if decision == "accept" else (value or "").strip()
            if decision == "correct" and (not reviewed or reviewed == row[0]):
                raise InvalidReview("A correction must provide a different non-empty value")
            if decision == "accept" and value not in (None, "", row[0]):
                raise InvalidReview("Accept cannot change the proposed value")
            reviewed_lineage = append_lineage_tx(connection, LineageInput(
                row[7],row[8],f"{row[6]}.{row[4]}",reviewed,row[6],row[2],
                extractor_provider=row[9],extractor_model=row[10],prompt_version=row[11],parser_version=row[12],
                correction_actor_id=actor.user_id,correction_reason=reason or ("Accepted proposal" if decision == "accept" else "Human correction"),
                predecessor_lineage_id=row[3],
            ))
            review_id = f"review-{uuid.uuid4().hex}"
            connection.extraction.execute(Statement.EXTRACTION_REVIEW_WRITE_EXTRACTION_FIELD_REVIEWS_003,
                (review_id,field_id,decision,row[0],reviewed,actor.user_id,reason,row[6],row[2],row[3],reviewed_lineage),
            )
            connection.extraction.execute(Statement.EXTRACTION_REVIEW_WRITE_EXTRACTION_FIELDS_004,
                (reviewed,actor.user_id,"accepted" if decision == "accept" else "corrected",field_id),
            )
            append_event_tx(connection,"field_corrected" if decision == "correct" else "field_reviewed","extraction_field",field_id,actor_id=actor.user_id,
                            organization_id=row[8],contract_id=row[7],payload={"decision":decision,"fieldName":row[4],"proposedValue":row[0],"reviewedValue":reviewed,"reviewId":review_id})
            connection.commit()
        return {"id":field_id,"decision":decision,"proposedValue":row[0],"reviewedValue":reviewed,"reviewId":review_id}

    with database() as connection:
        run = connection.extraction.execute(Statement.EXTRACTION_REVIEW_READ_EXTRACTION_FIELDS_EXTRACTION_RUNS_005, (field_id,)).fetchone()
    if not run: raise FileNotFoundError(field_id)
    return execute_authorized(actor, Action.UPDATE, extraction_scope(actor, run[0]), command)


def reviewed_value(field_id: str) -> str:
    with database() as connection:
        row = connection.extraction.execute(Statement.EXTRACTION_REVIEW_READ_EXTRACTION_FIELDS_006, (field_id,)).fetchone()
    if not row or row[1] not in {"accepted","corrected"}: raise UnreviewedField(field_id)
    return row[0]
