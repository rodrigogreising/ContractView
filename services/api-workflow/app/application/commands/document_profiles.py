"""Configuration-owned document-profile lifecycle and cluster confirmation."""

from __future__ import annotations

from copy import deepcopy
import json
import uuid
from typing import Any

from .access_scope import configuration_scope
from .provenance import append_event_tx
from ...authorization import Action, Actor, execute_authorized, require_permission
from ...domain.document_intake import (
    DocumentProfileError,
    EVALUATION_SUITE_VERSION,
    PARSER_VERSION,
    analyze_profile,
    content_hash,
    evaluate_profile,
    profile_content_hash,
    validate_fixture_suite,
    validate_profile_definition,
)
from ...shared_contracts import (
    DocumentProfileVersionContract,
    ProfileAssociationDto,
    ProfileEvaluationEvidenceContract,
    ProfileFixtureSetContract,
)
from ..ports.statements import Statement
from ..transaction import transaction as database


class InvalidDocumentProfile(ValueError):
    pass


def _rationale(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidDocumentProfile("A governance rationale is required")
    return normalized


def _profile_detail_tx(connection: Any, profile_version_id: str) -> dict[str, Any]:
    row = connection.configuration.execute(
        Statement.DOCUMENT_PROFILES_READ_DOCUMENT_PROFILE_ACTIVE_ASSIGNMENTS_DOCUMENT_PROFILE_APPROVALS_DOCUMENT_PROFILE_EVALUATIONS_DOCUMENT_PROFILE_FIXTURE_SETS_DOCUMENT_PROFILE_LIFECYCLE_EVENTS_DOCUMENT_PROFILE_VERSIONS_001,
        (profile_version_id,),
    ).fetchone()
    if not row:
        raise InvalidDocumentProfile("Document profile version was not found")
    payload = deepcopy(row[4])
    payload["lifecycle"] = row[11]
    if row[20]:
        payload["evaluationEvidence"] = {
            "kind": "profile_evaluation",
            "id": row[20],
            "version": row[21],
            "sha256": row[29],
        }
    profile = DocumentProfileVersionContract.model_validate(payload).model_dump(
        by_alias=True, mode="json"
    )
    evaluation = None
    if row[20]:
        evaluation = ProfileEvaluationEvidenceContract.model_validate(
            {
                "id": row[20],
                "profileVersion": {
                    "kind": "document_profile",
                    "id": row[0],
                    "version": row[3],
                    "sha256": row[5],
                },
                "fixtureSet": {
                    "kind": "profile_fixture_set",
                    "id": row[16],
                    "version": row[17],
                    "sha256": row[19],
                },
                "suiteVersion": row[21],
                "ocrVersion": row[22],
                "parserVersion": row[23],
                "results": row[24],
                "supportedFieldExactness": float(row[25]),
                "sourceLocationExactness": float(row[26]),
                "unknownSafeRoutingRate": float(row[27]),
                "passed": row[28],
                "resultHash": row[29],
            }
        ).model_dump(by_alias=True, mode="json")
    approval = None
    if row[35]:
        approval = {
            "id": row[35],
            "evaluationId": row[36],
            "approvedBy": row[37],
            "approvedRole": row[38],
            "approvedOrganizationId": row[39],
            "rationale": row[40],
            "approvalHash": row[41],
            "approvedAt": row[42].isoformat(),
        }
    return {
        "profile": profile,
        "state": row[11],
        "lastAction": row[12],
        "lastRationale": row[13],
        "lastEventHash": row[14],
        "lastTransitionAt": row[15].isoformat(),
        "fixtureSet": ProfileFixtureSetContract.model_validate(
            {
                "id": row[16],
                "version": row[17],
                "cases": row[18],
                "contentHash": row[19],
            }
        ).model_dump(by_alias=True, mode="json"),
        "evaluationEvidence": evaluation,
        "approval": approval,
        "activeConfigurationVersionId": row[43],
        "activatedAt": row[44].isoformat() if row[44] else None,
        "createdBy": row[7],
        "createdRole": row[8],
        "createdOrganizationId": row[9],
        "createdAt": row[10].isoformat(),
    }


def _validate_profile_evidence(details: dict[str, Any]) -> None:
    profile = details["profile"]
    fixture_set = details["fixtureSet"]
    evidence = details["evaluationEvidence"]
    approval = details["approval"]
    validate_profile_definition(profile)
    validate_fixture_suite(profile, fixture_set["cases"])
    expected_profile_hash = profile_content_hash(profile)
    expected_fixture_hash = content_hash(
        {
            "id": fixture_set["id"],
            "version": fixture_set["version"],
            "cases": fixture_set["cases"],
        }
    )
    if (
        expected_profile_hash != profile["contentHash"]
        or expected_fixture_hash != fixture_set["contentHash"]
        or profile["fixtureSet"]["sha256"] != expected_fixture_hash
    ):
        raise InvalidDocumentProfile("Profile or fixture content hash is not current")
    if not evidence:
        raise InvalidDocumentProfile("Successful immutable profile evaluation is required")
    expected_evaluation = evaluate_profile(
        profile,
        fixture_set["cases"],
        ocr_version=evidence["ocrVersion"],
    )
    for key in (
        "suiteVersion",
        "ocrVersion",
        "parserVersion",
        "results",
        "supportedFieldExactness",
        "sourceLocationExactness",
        "unknownSafeRoutingRate",
        "passed",
        "resultHash",
    ):
        if evidence[key] != expected_evaluation[key]:
            raise InvalidDocumentProfile("Profile evaluation evidence cannot be reproduced")
    if not approval or approval["evaluationId"] != evidence["id"]:
        raise InvalidDocumentProfile("Profile approval must bind the exact evaluation")
    approval_body = {
        "id": approval["id"],
        "profileVersionId": profile["id"],
        "evaluationId": evidence["id"],
        "approvedBy": approval["approvedBy"],
        "approvedRole": approval["approvedRole"],
        "approvedOrganizationId": approval["approvedOrganizationId"],
        "rationale": approval["rationale"],
    }
    if approval["approvalHash"] != content_hash(approval_body):
        raise InvalidDocumentProfile("Profile approval hash is invalid")


def validate_profile_references_tx(
    connection: Any,
    contract_id: str,
    references: list[dict[str, Any]],
    *,
    activation_action: str = "activate",
) -> list[dict[str, Any]]:
    if activation_action not in {"activate", "rollback"}:
        raise InvalidDocumentProfile("Unsupported profile activation action")
    details_by_key: dict[str, dict[str, Any]] = {}
    for reference in references:
        details = _profile_detail_tx(connection, reference.get("id", ""))
        profile = details["profile"]
        if profile["contractId"] != contract_id:
            raise InvalidDocumentProfile("Profile reference is outside the configuration contract")
        if (
            reference.get("kind") != "document_profile"
            or reference.get("version") != profile["version"]
            or reference.get("sha256") != profile["contentHash"]
        ):
            raise InvalidDocumentProfile(
                "Configuration must reference the exact profile version and hash"
            )
        activatable_states = {"approved", "active"}
        if activation_action == "rollback":
            activatable_states.update({"superseded", "retired"})
        if details["state"] not in activatable_states:
            raise InvalidDocumentProfile("Every configuration profile must be approved")
        _validate_profile_evidence(details)
        if profile["profileKey"] in details_by_key:
            raise InvalidDocumentProfile("Configuration profile keys must be unique")
        details_by_key[profile["profileKey"]] = details
    return list(details_by_key.values())


def _append_lifecycle_tx(
    connection: Any,
    actor: Actor,
    details: dict[str, Any],
    *,
    state: str,
    action: str,
    rationale: str,
    evaluation_id: str | None = None,
    approval_id: str | None = None,
    predecessor_id: str | None = None,
    successor_id: str | None = None,
    configuration_version_id: str | None = None,
) -> dict[str, Any]:
    profile = details["profile"]
    event_id = f"profile-lifecycle-{uuid.uuid4().hex}"
    body = {
        "id": event_id,
        "profileVersionId": profile["id"],
        "profileVersion": profile["version"],
        "state": state,
        "action": action,
        "actorId": actor.user_id,
        "actorRole": actor.role.value,
        "actorOrganizationId": actor.organization_id,
        "rationale": rationale,
        "evaluationId": evaluation_id,
        "approvalId": approval_id,
        "predecessorVersionId": predecessor_id,
        "successorVersionId": successor_id,
        "configurationVersionId": configuration_version_id,
    }
    event_hash = content_hash(body)
    connection.configuration.execute(
        Statement.DOCUMENT_PROFILES_WRITE_DOCUMENT_PROFILE_LIFECYCLE_EVENTS_008,
        (
            event_id,
            profile["id"],
            profile["contractId"],
            state,
            action,
            actor.user_id,
            actor.role.value,
            actor.organization_id,
            rationale,
            evaluation_id,
            approval_id,
            predecessor_id,
            successor_id,
            configuration_version_id,
            event_hash,
        ),
    )
    event_type = {
        "create": "profile_drafted",
        "test": "profile_tested",
        "approve_configuration": "profile_approved",
        "activate": "profile_activated",
        "rollback": "profile_rollback_activated",
        "supersede": "profile_superseded",
        "retire": "profile_retired",
    }[action]
    append_event_tx(
        connection,
        event_type,
        "document_profile_version",
        profile["id"],
        actor_id=actor.user_id,
        organization_id=actor.organization_id,
        contract_id=profile["contractId"],
        payload={**body, "eventHash": event_hash},
        version_references=[
            {
                "kind": "document_profile",
                "id": profile["id"],
                "version": profile["version"],
                "sha256": profile["contentHash"],
            }
        ],
    )
    return {**body, "eventHash": event_hash}


def create_profile_draft(
    actor: Actor,
    contract_id: str,
    definition: dict[str, Any],
    fixtures: list[dict[str, Any]],
    rationale: str,
) -> dict[str, Any]:
    rationale = _rationale(rationale)

    def command() -> dict[str, Any]:
        profile_key = str(definition.get("profileKey", "")).strip()
        if not profile_key:
            raise InvalidDocumentProfile("profileKey is required")
        try:
            validate_profile_definition(definition)
            validated_fixtures = validate_fixture_suite(definition, fixtures)
        except DocumentProfileError as error:
            raise InvalidDocumentProfile(str(error)) from error
        with database() as connection:
            version_row = connection.configuration.execute(
                Statement.DOCUMENT_PROFILES_READ_DOCUMENT_PROFILE_VERSIONS_003,
                (contract_id, profile_key),
            ).fetchone()
            if version_row is None:
                raise InvalidDocumentProfile("Could not allocate a profile version")
            version = version_row[0]
            profile_id = f"profile-{profile_key}-v{version}-{uuid.uuid4().hex[:8]}"
            fixture_set_id = f"fixture-set-{profile_key}-v{version}-{uuid.uuid4().hex[:8]}"
            predecessor_id = definition.get("predecessorVersionId")
            predecessor_reference = None
            if version > 1 and not predecessor_id:
                raise InvalidDocumentProfile(
                    "A successor profile must reference its exact predecessor"
                )
            if predecessor_id:
                predecessor = _profile_detail_tx(connection, predecessor_id)
                predecessor_profile = predecessor["profile"]
                if (
                    predecessor_profile["contractId"] != contract_id
                    or predecessor_profile["profileKey"] != profile_key
                    or predecessor_profile["version"] != version - 1
                ):
                    raise InvalidDocumentProfile(
                        "Profile predecessor must be the exact prior version of the same profile key"
                    )
                if predecessor["state"] not in {
                    "approved",
                    "active",
                    "superseded",
                    "retired",
                }:
                    raise InvalidDocumentProfile(
                        "Profile predecessor must have completed human approval"
                    )
                predecessor_reference = {
                    "kind": "document_profile",
                    "id": predecessor_id,
                    "version": predecessor_profile["version"],
                    "sha256": predecessor_profile["contentHash"],
                }
            draft = {
                "id": profile_id,
                "contractId": contract_id,
                "profileKey": profile_key,
                "version": version,
                "lifecycle": "draft",
                "artifactClass": definition.get("artifactClass"),
                "languageTag": definition.get("languageTag"),
                "vendorAliases": definition.get("vendorAliases", []),
                "requiredFields": definition.get("requiredFields", []),
                "ledgerMatchRule": definition.get("ledgerMatchRule", {}),
                "fingerprintSpecification": definition.get("fingerprintSpecification", {}),
                "acceptedFingerprints": sorted(
                    {
                        analyze_profile(definition, item["ocrText"], item["mediaType"]).fingerprint
                        for item in validated_fixtures
                        if item["caseKind"] == "supported_layout"
                    }
                ),
                "fixtureSet": {
                    "kind": "profile_fixture_set",
                    "id": fixture_set_id,
                    "version": str(version),
                },
                "evaluationEvidence": None,
                "predecessor": predecessor_reference,
            }
            fixture_body = {
                "id": fixture_set_id,
                "version": str(version),
                "cases": validated_fixtures,
            }
            fixture_hash = content_hash(fixture_body)
            draft["fixtureSet"]["sha256"] = fixture_hash
            draft["contentHash"] = profile_content_hash(draft)
            profile = DocumentProfileVersionContract.model_validate(draft).model_dump(
                by_alias=True, mode="json"
            )
            fixture_set = ProfileFixtureSetContract.model_validate(
                {**fixture_body, "contentHash": fixture_hash}
            ).model_dump(by_alias=True, mode="json")
            connection.configuration.execute(
                Statement.DOCUMENT_PROFILES_WRITE_DOCUMENT_PROFILE_VERSIONS_004,
                (
                    profile_id,
                    contract_id,
                    profile_key,
                    version,
                    json.dumps(profile),
                    profile["contentHash"],
                    predecessor_id,
                    actor.user_id,
                    actor.role.value,
                    actor.organization_id,
                ),
            )
            connection.configuration.execute(
                Statement.DOCUMENT_PROFILES_WRITE_DOCUMENT_PROFILE_FIXTURE_SETS_005,
                (
                    fixture_set_id,
                    profile_id,
                    contract_id,
                    str(version),
                    json.dumps(validated_fixtures),
                    fixture_hash,
                    actor.user_id,
                ),
            )
            details = {"profile": profile}
            _append_lifecycle_tx(
                connection,
                actor,
                details,
                state="draft",
                action="create",
                rationale=rationale,
                predecessor_id=predecessor_id,
            )
            connection.commit()
        return profile_detail(actor, profile_id)

    return execute_authorized(
        actor, Action.CREATE, configuration_scope(actor, contract_id), command
    )


def test_profile(actor: Actor, profile_version_id: str, rationale: str) -> dict[str, Any]:
    rationale = _rationale(rationale)
    with database() as connection:
        initial = _profile_detail_tx(connection, profile_version_id)

    def command() -> dict[str, Any]:
        with database() as connection:
            details = _profile_detail_tx(connection, profile_version_id)
            if details["state"] != "draft":
                raise InvalidDocumentProfile("Only a draft profile may be tested")
            evaluation = evaluate_profile(
                details["profile"],
                details["fixtureSet"]["cases"],
                ocr_version="fixture-transcript-v1",
            )
            evidence_id = f"profile-evaluation-{uuid.uuid4().hex}"
            evidence = ProfileEvaluationEvidenceContract.model_validate(
                {
                    "id": evidence_id,
                    "profileVersion": {
                        "kind": "document_profile",
                        "id": profile_version_id,
                        "version": details["profile"]["version"],
                        "sha256": details["profile"]["contentHash"],
                    },
                    "fixtureSet": details["profile"]["fixtureSet"],
                    **evaluation,
                }
            ).model_dump(by_alias=True, mode="json")
            connection.configuration.execute(
                Statement.DOCUMENT_PROFILES_WRITE_DOCUMENT_PROFILE_EVALUATIONS_006,
                (
                    evidence_id,
                    profile_version_id,
                    details["fixtureSet"]["id"],
                    details["profile"]["contractId"],
                    EVALUATION_SUITE_VERSION,
                    evidence["ocrVersion"],
                    PARSER_VERSION,
                    json.dumps(evidence["results"]),
                    evidence["supportedFieldExactness"],
                    evidence["sourceLocationExactness"],
                    evidence["unknownSafeRoutingRate"],
                    evidence["passed"],
                    evidence["resultHash"],
                    actor.user_id,
                    actor.role.value,
                    actor.organization_id,
                    rationale,
                ),
            )
            _append_lifecycle_tx(
                connection,
                actor,
                details,
                state="tested",
                action="test",
                rationale=rationale,
                evaluation_id=evidence_id,
            )
            connection.commit()
        return profile_detail(actor, profile_version_id)

    return execute_authorized(
        actor,
        Action.TEST,
        configuration_scope(actor, initial["profile"]["contractId"]),
        command,
    )


def approve_profile(actor: Actor, profile_version_id: str, rationale: str) -> dict[str, Any]:
    rationale = _rationale(rationale)
    with database() as connection:
        initial = _profile_detail_tx(connection, profile_version_id)

    def command() -> dict[str, Any]:
        with database() as connection:
            details = _profile_detail_tx(connection, profile_version_id)
            evidence = details["evaluationEvidence"]
            if details["state"] != "tested" or not evidence or not evidence["passed"]:
                raise InvalidDocumentProfile(
                    "Only a tested profile with successful immutable evaluation evidence may be approved"
                )
            if (
                evidence["supportedFieldExactness"] != 1.0
                or evidence["sourceLocationExactness"] != 1.0
                or evidence["unknownSafeRoutingRate"] != 1.0
            ):
                raise InvalidDocumentProfile("Profile evaluation does not meet exact MVP thresholds")
            approval_id = f"profile-approval-{uuid.uuid4().hex}"
            approval_body = {
                "id": approval_id,
                "profileVersionId": profile_version_id,
                "evaluationId": evidence["id"],
                "approvedBy": actor.user_id,
                "approvedRole": actor.role.value,
                "approvedOrganizationId": actor.organization_id,
                "rationale": rationale,
            }
            approval_hash = content_hash(approval_body)
            connection.configuration.execute(
                Statement.DOCUMENT_PROFILES_WRITE_DOCUMENT_PROFILE_APPROVALS_007,
                (
                    approval_id,
                    profile_version_id,
                    evidence["id"],
                    details["profile"]["contractId"],
                    actor.user_id,
                    actor.role.value,
                    actor.organization_id,
                    rationale,
                    approval_hash,
                ),
            )
            _append_lifecycle_tx(
                connection,
                actor,
                details,
                state="approved",
                action="approve_configuration",
                rationale=rationale,
                evaluation_id=evidence["id"],
                approval_id=approval_id,
            )
            connection.commit()
        return profile_detail(actor, profile_version_id)

    return execute_authorized(
        actor,
        Action.APPROVE_CONFIGURATION,
        configuration_scope(actor, initial["profile"]["contractId"]),
        command,
    )


def activate_profile_references_tx(
    connection: Any,
    actor: Actor,
    contract_id: str,
    configuration_version_id: str,
    references: list[dict[str, Any]],
    rationale: str,
    *,
    activation_action: str = "activate",
) -> None:
    validated = validate_profile_references_tx(
        connection,
        contract_id,
        references,
        activation_action=activation_action,
    )
    for details in validated:
        profile = details["profile"]
        current = connection.configuration.execute(
            Statement.DOCUMENT_PROFILES_READ_DOCUMENT_PROFILE_ACTIVE_ASSIGNMENTS_009,
            (contract_id, profile["profileKey"]),
        ).fetchone()
        if current and current[0] != profile["id"]:
            previous = _profile_detail_tx(connection, current[0])
            _append_lifecycle_tx(
                connection,
                actor,
                previous,
                state="superseded",
                action="supersede",
                rationale=rationale,
                successor_id=profile["id"],
                configuration_version_id=configuration_version_id,
            )
        connection.configuration.execute(
            Statement.DOCUMENT_PROFILES_WRITE_DOCUMENT_PROFILE_ACTIVE_ASSIGNMENTS_010,
            (
                contract_id,
                profile["profileKey"],
                profile["id"],
                configuration_version_id,
                actor.user_id,
                actor.role.value,
                actor.organization_id,
            ),
        )
        if not current or current[0] != profile["id"]:
            _append_lifecycle_tx(
                connection,
                actor,
                details,
                state="active",
                action=activation_action,
                rationale=rationale,
                predecessor_id=profile.get("predecessor", {}).get("id") if profile.get("predecessor") else None,
                configuration_version_id=configuration_version_id,
            )


def retire_profile(actor: Actor, profile_version_id: str, rationale: str) -> dict[str, Any]:
    rationale = _rationale(rationale)
    with database() as connection:
        initial = _profile_detail_tx(connection, profile_version_id)

    def command() -> dict[str, Any]:
        with database() as connection:
            details = _profile_detail_tx(connection, profile_version_id)
            if details["state"] not in {"approved", "superseded"} or details["activeConfigurationVersionId"]:
                raise InvalidDocumentProfile("Only a non-active approved or superseded profile may be retired")
            _append_lifecycle_tx(
                connection,
                actor,
                details,
                state="retired",
                action="retire",
                rationale=rationale,
            )
            connection.commit()
        return profile_detail(actor, profile_version_id)

    return execute_authorized(
        actor,
        Action.RETIRE,
        configuration_scope(actor, initial["profile"]["contractId"]),
        command,
    )


def list_profiles(actor: Actor, contract_id: str) -> list[dict[str, Any]]:
    require_permission(actor, Action.READ, configuration_scope(actor, contract_id))
    with database() as connection:
        ids = connection.configuration.execute(
            Statement.DOCUMENT_PROFILES_READ_DOCUMENT_PROFILE_VERSIONS_002,
            (contract_id,),
        ).fetchall()
        return [_profile_detail_tx(connection, row[0]) for row in ids]


def profile_detail(actor: Actor, profile_version_id: str) -> dict[str, Any]:
    with database() as connection:
        details = _profile_detail_tx(connection, profile_version_id)
    require_permission(
        actor,
        Action.READ,
        configuration_scope(actor, details["profile"]["contractId"]),
    )
    return details


def list_cluster_suggestions(actor: Actor, contract_id: str) -> list[dict[str, Any]]:
    require_permission(actor, Action.READ, configuration_scope(actor, contract_id))
    with database() as connection:
        rows = connection.read_models.execute(
            Statement.DOCUMENT_PROFILES_READ_ARTIFACTS_DOCUMENT_CLUSTER_PROJECTIONS_DOCUMENT_FINGERPRINTS_DOCUMENT_PROFILE_CLUSTER_ASSOCIATIONS_013,
            (contract_id,),
        ).fetchall()
    return [
        {
            "id": row[0],
            "clusterKey": row[1],
            "languageTag": row[2],
            "status": "confirmed_as_draft" if row[14] else row[3],
            "canonical": row[4],
            "projectionHash": row[5],
            "createdAt": row[6].isoformat(),
            "fingerprint": {
                "id": row[7],
                "specificationVersion": row[8],
                "sha256": row[9],
            },
            "sourceArtifact": {"id": row[10], "filename": row[11], "sha256": row[12]},
            "memberCount": row[13],
            "association": (
                {
                    "id": row[14],
                    "profileKey": row[15],
                    "status": row[16],
                    "confirmedBy": row[17],
                    "confirmedRole": row[18],
                    "confirmedOrganizationId": row[19],
                    "rationale": row[20],
                    "associationHash": row[21],
                    "createdAt": row[22].isoformat(),
                }
                if row[14]
                else None
            ),
        }
        for row in rows
    ]


def confirm_cluster(
    actor: Actor, cluster_projection_id: str, profile_key: str, rationale: str
) -> dict[str, Any]:
    rationale = _rationale(rationale)
    with database() as connection:
        cluster = connection.extraction.execute(
            Statement.DOCUMENT_PROFILES_READ_DOCUMENT_CLUSTER_PROJECTIONS_011,
            (cluster_projection_id,),
        ).fetchone()
    if not cluster:
        raise InvalidDocumentProfile("Cluster projection was not found")

    def command() -> dict[str, Any]:
        with database() as connection:
            current = connection.extraction.execute(
                Statement.DOCUMENT_PROFILES_READ_DOCUMENT_CLUSTER_PROJECTIONS_011,
                (cluster_projection_id,),
            ).fetchone()
            if current != cluster:
                raise InvalidDocumentProfile("Cluster projection changed")
            association_id = f"profile-association-{uuid.uuid4().hex}"
            body = {
                "id": association_id,
                "contractId": cluster[1],
                "clusterProjectionId": cluster_projection_id,
                "clusterKey": cluster[0],
                "profileKey": profile_key.strip(),
                "status": "draft",
                "confirmedBy": actor.user_id,
                "confirmedRole": actor.role.value,
                "confirmedOrganizationId": actor.organization_id,
                "rationale": rationale,
            }
            if not body["profileKey"]:
                raise InvalidDocumentProfile("profileKey is required")
            association_hash = content_hash(body)
            created_row = connection.configuration.execute(
                Statement.DOCUMENT_PROFILES_WRITE_DOCUMENT_PROFILE_CLUSTER_ASSOCIATIONS_012,
                (
                    association_id,
                    cluster[1],
                    cluster[0],
                    body["profileKey"],
                    actor.user_id,
                    actor.role.value,
                    actor.organization_id,
                    rationale,
                    association_hash,
                ),
            ).fetchone()
            if created_row is None:
                raise InvalidDocumentProfile("Could not persist the draft association")
            created_at = created_row[0]
            append_event_tx(
                connection,
                "cluster_confirmed",
                "document_cluster_projection",
                cluster_projection_id,
                actor_id=actor.user_id,
                organization_id=actor.organization_id,
                contract_id=cluster[1],
                payload={**body, "associationHash": association_hash},
                version_references=[
                    {
                        "kind": "cluster_projection",
                        "id": cluster_projection_id,
                        "version": 1,
                    }
                ],
            )
            connection.commit()
        return ProfileAssociationDto(
            id=association_id,
            contract_id=cluster[1],
            cluster_projection={
                "kind": "cluster_projection",
                "id": cluster_projection_id,
                "version": 1,
            },
            profile_key=body["profileKey"],
            status="draft",
            confirmed_by={
                "userId": actor.user_id,
                "organizationId": actor.organization_id,
                "role": actor.role.value,
            },
            rationale=rationale,
            created_at=created_at,
        ).model_dump(by_alias=True, mode="json")

    return execute_authorized(
        actor,
        Action.UPDATE,
        configuration_scope(actor, cluster[1]),
        command,
    )
