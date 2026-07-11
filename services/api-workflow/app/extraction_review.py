from dataclasses import dataclass
import uuid

from .authorization import Action, Actor, ResourceKind, ResourceScope, execute_authorized, require_permission
from .provenance import LineageInput, append_event_tx, append_lineage_tx
from .runtime import database


class InvalidReview(ValueError): pass
class UnreviewedField(ValueError): pass


def _scope(resource_id: str, organization_id: str) -> ResourceScope:
    return ResourceScope(resource_id, ResourceKind.JOB, organization_id, ngo_organization_id=organization_id)


def list_extractions(actor: Actor, contract_id: str) -> list[dict]:
    with database() as connection:
        rows = connection.execute(
            """select r.id,r.source_artifact_id,a.filename,r.provider,r.model,r.status,r.routing_reason,
                      f.id,f.field_name,f.proposed_value,f.reviewed_value,f.confidence,f.source_location,f.review_status
               from extraction_runs r join artifacts a on a.id=r.source_artifact_id
               join extraction_fields f on f.extraction_run_id=r.id
               where r.contract_id=%s and r.status='needs_review' order by r.created_at,f.field_name""", (contract_id,)
        ).fetchall()
    grouped: dict[str, dict] = {}
    for row in rows:
        require_permission(actor, Action.READ, _scope(row[0], actor.organization_id if actor.role.value == "auditor" else _organization_for_run(row[0])))
        item = grouped.setdefault(row[0], {"id":row[0],"sourceArtifactId":row[1],"filename":row[2],"provider":row[3],"model":row[4],"status":row[5],"routingReason":row[6],"fields":[]})
        item["fields"].append({"id":row[7],"name":row[8],"proposedValue":row[9],"reviewedValue":row[10],"confidence":str(row[11]),"sourceLocation":row[12],"reviewStatus":row[13]})
    return list(grouped.values())


def _organization_for_run(run_id: str) -> str:
    with database() as connection:
        return connection.execute("select organization_id from extraction_runs where id=%s", (run_id,)).fetchone()[0]


def review_field(actor: Actor, field_id: str, decision: str, value: str | None = None, reason: str | None = None) -> dict:
    if decision not in {"accept", "correct"}: raise InvalidReview("Decision must be accept or correct")

    def command() -> dict:
        with database() as connection:
            row = connection.execute(
                """select f.proposed_value,f.review_status,f.source_location,f.proposed_lineage_id,f.field_name,
                          r.id,r.source_artifact_id,r.contract_id,r.organization_id,r.provider,r.model,r.prompt_version,r.parser_version
                   from extraction_fields f join extraction_runs r on r.id=f.extraction_run_id
                   where f.id=%s for update""", (field_id,)
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
            connection.execute(
                """insert into extraction_field_reviews
                   (id,extraction_field_id,decision,proposed_value,reviewed_value,actor_id,reason,source_artifact_id,source_location,predecessor_lineage_id,reviewed_lineage_id)
                   values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (review_id,field_id,decision,row[0],reviewed,actor.user_id,reason,row[6],row[2],row[3],reviewed_lineage),
            )
            connection.execute(
                "update extraction_fields set reviewed_value=%s,reviewed_by=%s,reviewed_at=now(),review_status=%s where id=%s",
                (reviewed,actor.user_id,"accepted" if decision == "accept" else "corrected",field_id),
            )
            append_event_tx(connection,"field_reviewed","extraction_field",field_id,actor_id=actor.user_id,
                            organization_id=row[8],contract_id=row[7],payload={"decision":decision,"fieldName":row[4],"proposedValue":row[0],"reviewedValue":reviewed,"reviewId":review_id})
            connection.commit()
        return {"id":field_id,"decision":decision,"proposedValue":row[0],"reviewedValue":reviewed,"reviewId":review_id}

    with database() as connection:
        org = connection.execute("select r.organization_id from extraction_fields f join extraction_runs r on r.id=f.extraction_run_id where f.id=%s", (field_id,)).fetchone()
    if not org: raise FileNotFoundError(field_id)
    return execute_authorized(actor, Action.UPDATE, _scope(field_id, org[0]), command)


def reviewed_value(field_id: str) -> str:
    with database() as connection:
        row = connection.execute("select reviewed_value,review_status from extraction_fields where id=%s", (field_id,)).fetchone()
    if not row or row[1] not in {"accepted","corrected"}: raise UnreviewedField(field_id)
    return row[0]
