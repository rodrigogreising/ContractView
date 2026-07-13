from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any, Protocol
import uuid

from .artifacts import Artifact, read_and_verify_artifact, store_artifact
from ...authorization import Actor, Role
from ...domain.document_intake import (
    FINGERPRINT_ALGORITHM,
    FINGERPRINT_SPECIFICATION_VERSION,
    PARSER_VERSION,
    cluster_fingerprint,
    content_hash,
    exact_profile_match,
    ledger_expense_key,
    ledger_values_match,
)
from ...shared_contracts import DocumentIntakeResultDto
from .ingestion import IngestionJob
from .provenance import LineageInput, append_event_tx, append_lineage_tx
from ..ports.statements import Statement
from ..transaction import transaction as database
from ..extraction_provider import extraction_adapter

PROMPT_VERSION = "not-applicable-deterministic-profile-v1"
SCHEMA_VERSION = "document-intake-result-v1"
REVIEW_THRESHOLD = Decimal("0.8500")


class ExtractionProviderError(RuntimeError):
    pass


class InvalidExtractionResponse(ValueError):
    pass


@dataclass(frozen=True)
class OcrResponse:
    provider: str
    model: str
    text: str
    confidence: Decimal
    source_location: str = "page=1"


class OcrAdapter(Protocol):
    def extract(self, filename: str, media_type: str, content: bytes) -> OcrResponse: ...


def _runtime_profiles(contract_id: str) -> tuple[dict | None, list[dict]]:
    with database() as connection:
        rows = connection.configuration.execute(
            Statement.EXTRACTION_READ_CONFIGURATION_ACTIVE_VERSIONS_CONFIGURATION_VERSIONS_DOCUMENT_PROFILE_VERSIONS_004,
            (contract_id,),
        ).fetchall()
    if not rows:
        return None, []
    return {"id": rows[0][0], "version": rows[0][1]}, [row[4] for row in rows]


def _record_failure(
    job: IngestionJob,
    artifact: Artifact,
    provider: str,
    model: str,
    message: str,
) -> None:
    run_id = f"extraction-{uuid.uuid4().hex}"
    with database() as connection:
        connection.extraction.execute(
            Statement.EXTRACTION_WRITE_EXTRACTION_RUNS_001,
            (
                run_id,
                job.id,
                artifact.id,
                job.contract_id,
                job.organization_id,
                provider,
                model,
                PROMPT_VERSION,
                PARSER_VERSION,
                SCHEMA_VERSION,
                message,
            ),
        )
        append_event_tx(
            connection,
            "extraction_failed",
            "extraction_run",
            run_id,
            actor_id=artifact.created_by,
            organization_id=job.organization_id,
            contract_id=job.contract_id,
            payload={
                "artifactId": artifact.id,
                "artifactHash": artifact.sha256,
                "ocrVersion": model,
                "parserVersion": PARSER_VERSION,
                "error": message,
            },
            version_references=[
                {
                    "kind": "artifact",
                    "id": artifact.id,
                    "version": 1,
                    "sha256": artifact.sha256,
                },
                {"kind": "extraction_run", "id": run_id, "version": SCHEMA_VERSION},
            ],
        )
        connection.commit()


def _ledger_match(
    connection,
    contract_id: str,
    profile: dict[str, Any],
    fields: dict[str, str],
) -> tuple[str, str | None]:
    expense_key = ledger_expense_key(profile, fields)
    if not expense_key:
        return (
            "unmatched" if profile["ledgerMatchRule"]["required"] else "not_evaluated",
            None,
        )
    rows = connection.extraction.execute(
        Statement.EXTRACTION_READ_EXPENSE_ROWS_007,
        (contract_id, expense_key),
    ).fetchall()
    if not rows:
        return "unmatched", expense_key
    if len(rows) > 1:
        return "ambiguous", expense_key
    row = rows[0]
    return (
        "matched"
        if ledger_values_match(
            profile,
            fields,
            expense_date=row[1],
            vendor=row[2],
            amount=row[3],
        )
        else "unmatched",
        expense_key,
    )


def extract_evidence(
    job: IngestionJob, artifact: Artifact, adapter: OcrAdapter | None = None
) -> dict:
    adapter = adapter or extraction_adapter()
    content = read_and_verify_artifact(artifact)
    try:
        response = adapter.extract(artifact.filename, artifact.media_type, content)
        if not response.text.strip():
            raise InvalidExtractionResponse("OCR returned no usable text")
    except Exception as error:
        _record_failure(
            job,
            artifact,
            getattr(adapter, "provider", "unknown"),
            getattr(adapter, "model", "unknown"),
            str(error),
        )
        raise

    raw = json.dumps(
        {
            "provider": response.provider,
            "model": response.model,
            "text": response.text,
            "confidence": str(response.confidence),
            "sourceLocation": response.source_location,
            "promptVersion": PROMPT_VERSION,
            "parserVersion": PARSER_VERSION,
        },
        sort_keys=True,
    ).encode()
    actor = Actor(artifact.created_by, artifact.organization_id, Role.NGO_PREPARER)
    raw_artifact = store_artifact(
        actor,
        artifact.contract_id,
        f"{artifact.id}-ocr-response.json",
        "application/json",
        raw,
        artifact_kind="generated",
        predecessor_id=artifact.id,
        relation_type="derived_from",
    )

    configuration, profiles = _runtime_profiles(job.contract_id)
    matched = exact_profile_match(profiles, response.text, artifact.media_type)
    if matched:
        profile, analysis = matched
        outcome = "recognized_profile_draft"
        match_kind = "exact"
        fields = {item.name: item.value for item in analysis.fields}
        field_contracts = list(analysis.fields)
        fingerprint_signals = analysis.signals
        fingerprint_sha = analysis.fingerprint
        reason = "Exact active profile fingerprint and required fields matched"
    else:
        profile = None
        fields = {}
        field_contracts = []
        fingerprint_signals, fingerprint_sha = cluster_fingerprint(
            response.text, artifact.media_type
        )
        outcome = "needs_profile_review"
        match_kind = "none"
        reason = "No exact active profile fingerprint matched; configuration review is required"

    run_id = f"extraction-{uuid.uuid4().hex}"
    fingerprint_id = f"document-fingerprint-{uuid.uuid4().hex}"
    match_id = f"profile-match-{uuid.uuid4().hex}"
    cluster_id = None
    routing = "LOW_CONFIDENCE" if response.confidence < REVIEW_THRESHOLD else outcome
    with database() as connection:
        connection.extraction.execute(
            Statement.EXTRACTION_WRITE_EXTRACTION_RUNS_002,
            (
                run_id,
                job.id,
                artifact.id,
                raw_artifact.id,
                job.contract_id,
                job.organization_id,
                response.provider,
                response.model,
                PROMPT_VERSION,
                PARSER_VERSION,
                SCHEMA_VERSION,
                response.source_location,
                response.confidence,
                routing,
            ),
        )
        connection.extraction.execute(
            Statement.EXTRACTION_WRITE_DOCUMENT_FINGERPRINTS_004,
            (
                fingerprint_id,
                run_id,
                artifact.id,
                job.contract_id,
                artifact.sha256,
                FINGERPRINT_SPECIFICATION_VERSION,
                FINGERPRINT_ALGORITHM,
                profile["languageTag"] if profile else fingerprint_signals["languageTag"],
                json.dumps(fingerprint_signals),
                fingerprint_sha,
                response.model,
                PARSER_VERSION,
            ),
        )
        ledger_outcome, ledger_expense_key = (
            _ledger_match(connection, job.contract_id, profile, fields)
            if profile is not None
            else ("not_evaluated", None)
        )
        semantic_result = {
            "artifactHash": artifact.sha256,
            "rawOcrArtifactHash": raw_artifact.sha256,
            "ocrVersion": response.model,
            "parserVersion": PARSER_VERSION,
            "fingerprintSpecificationVersion": FINGERPRINT_SPECIFICATION_VERSION,
            "fingerprint": fingerprint_sha,
            "configurationVersion": configuration,
            "profileVersion": (
                {
                    "id": profile["id"],
                    "version": profile["version"],
                    "sha256": profile["contentHash"],
                }
                if profile
                else None
            ),
            "outcome": outcome,
            "matchKind": match_kind,
            "ledgerMatchOutcome": ledger_outcome,
            "ledgerExpenseKey": ledger_expense_key,
            "fields": [
                {
                    "name": item.name,
                    "fieldType": item.field_type,
                    "value": item.value,
                    "sourceLocation": item.source_location,
                }
                for item in field_contracts
            ],
        }
        result_hash = content_hash(semantic_result)
        connection.extraction.execute(
            Statement.EXTRACTION_WRITE_DOCUMENT_PROFILE_MATCH_RESULTS_005,
            (
                match_id,
                run_id,
                fingerprint_id,
                job.contract_id,
                outcome,
                match_kind,
                profile["id"] if profile else None,
                configuration["id"] if configuration else None,
                ledger_outcome,
                ledger_expense_key,
                reason,
                result_hash,
            ),
        )
        cluster_payload = None
        if not matched:
            cluster_id = f"document-cluster-{uuid.uuid4().hex}"
            projection_body = {
                "contractId": job.contract_id,
                "clusterKey": fingerprint_sha,
                "languageTag": fingerprint_signals["languageTag"],
                "artifactHash": artifact.sha256,
                "fingerprint": fingerprint_sha,
                "canonical": False,
            }
            projection_hash = content_hash(projection_body)
            connection.extraction.execute(
                Statement.EXTRACTION_WRITE_DOCUMENT_CLUSTER_PROJECTIONS_006,
                (
                    cluster_id,
                    job.contract_id,
                    fingerprint_id,
                    artifact.id,
                    fingerprint_sha,
                    fingerprint_signals["languageTag"],
                    projection_hash,
                ),
            )
            cluster_payload = {
                "id": cluster_id,
                "contractId": job.contract_id,
                "fingerprint": {
                    "kind": "document_fingerprint",
                    "id": fingerprint_id,
                    "version": FINGERPRINT_SPECIFICATION_VERSION,
                    "sha256": fingerprint_sha,
                },
                "languageTag": fingerprint_signals["languageTag"],
                "memberArtifacts": [
                    {
                        "kind": "artifact",
                        "id": artifact.id,
                        "version": 1,
                        "sha256": artifact.sha256,
                    }
                ],
                "status": "suggested",
                "canonical": False,
                "projectionHash": projection_hash,
            }

        field_payloads = []
        for item in field_contracts:
            field_id = f"field-{uuid.uuid4().hex}"
            proposed_lineage_id = append_lineage_tx(
                connection,
                LineageInput(
                    job.contract_id,
                    job.organization_id,
                    f"{artifact.id}.{item.name}",
                    item.value,
                    artifact.id,
                    item.source_location,
                    extractor_provider=response.provider,
                    extractor_model=response.model,
                    prompt_version=PROMPT_VERSION,
                    parser_version=PARSER_VERSION,
                ),
            )
            connection.extraction.execute(
                Statement.EXTRACTION_WRITE_EXTRACTION_FIELDS_003,
                (
                    field_id,
                    run_id,
                    item.name,
                    item.value,
                    response.confidence,
                    item.source_location,
                    proposed_lineage_id,
                ),
            )
            field_payloads.append(
                {
                    "name": item.name,
                    "fieldType": item.field_type,
                    "value": item.value,
                    "sourceLocation": {
                        "page": 1,
                        "line": item.source_line,
                        "label": item.source_label,
                        "canonical": item.source_location,
                    },
                    "confidence": float(response.confidence),
                }
            )

        version_references: list[dict[str, Any]] = [
            {
                "kind": "artifact",
                "id": artifact.id,
                "version": 1,
                "sha256": artifact.sha256,
            },
            {
                "kind": "artifact",
                "id": raw_artifact.id,
                "version": 1,
                "sha256": raw_artifact.sha256,
            },
            {
                "kind": "document_fingerprint",
                "id": fingerprint_id,
                "version": FINGERPRINT_SPECIFICATION_VERSION,
                "sha256": fingerprint_sha,
            },
            {"kind": "extraction_run", "id": run_id, "version": SCHEMA_VERSION},
        ]
        if profile:
            version_references.append(
                {
                    "kind": "document_profile",
                    "id": profile["id"],
                    "version": profile["version"],
                    "sha256": profile["contentHash"],
                }
            )
        if configuration:
            version_references.append(
                {
                    "kind": "configuration",
                    "id": configuration["id"],
                    "version": configuration["version"],
                }
            )
        if cluster_id:
            version_references.append(
                {"kind": "cluster_projection", "id": cluster_id, "version": 1}
            )
        event_payload = {
            "sourceArtifactId": artifact.id,
            "sourceArtifactHash": artifact.sha256,
            "rawResponseArtifactId": raw_artifact.id,
            "rawResponseArtifactHash": raw_artifact.sha256,
            "ocrVersion": response.model,
            "parserVersion": PARSER_VERSION,
            "fingerprintSpecificationVersion": FINGERPRINT_SPECIFICATION_VERSION,
            "fingerprintId": fingerprint_id,
            "fingerprint": fingerprint_sha,
            "profileVersionId": profile["id"] if profile else None,
            "configurationVersionId": configuration["id"] if configuration else None,
            "outcome": outcome,
            "ledgerMatchOutcome": ledger_outcome,
            "ledgerExpenseKey": ledger_expense_key,
            "clusterProjectionId": cluster_id,
            "resultHash": result_hash,
        }
        append_event_tx(
            connection,
            "document_routed",
            "extraction_run",
            run_id,
            actor_id=artifact.created_by,
            organization_id=job.organization_id,
            contract_id=job.contract_id,
            payload=event_payload,
            version_references=version_references,
        )
        if matched:
            append_event_tx(
                connection,
                "extraction_drafted",
                "extraction_run",
                run_id,
                actor_id=artifact.created_by,
                organization_id=job.organization_id,
                contract_id=job.contract_id,
                payload=event_payload,
                version_references=version_references,
            )
        connection.commit()

    result = DocumentIntakeResultDto(
        extraction_run_id=run_id,
        source_artifact={
            "kind": "artifact",
            "id": artifact.id,
            "version": 1,
            "sha256": artifact.sha256,
        },
        raw_ocr_artifact={
            "kind": "artifact",
            "id": raw_artifact.id,
            "version": 1,
            "sha256": raw_artifact.sha256,
        },
        ocr_version=response.model,
        parser_version=PARSER_VERSION,
        fingerprint={
            "id": fingerprint_id,
            "artifact": {
                "kind": "artifact",
                "id": artifact.id,
                "version": 1,
                "sha256": artifact.sha256,
            },
            "specificationVersion": FINGERPRINT_SPECIFICATION_VERSION,
            "algorithm": FINGERPRINT_ALGORITHM,
            "languageTag": profile["languageTag"] if profile else fingerprint_signals["languageTag"],
            "signals": fingerprint_signals,
            "sha256": fingerprint_sha,
        },
        match={
            "id": match_id,
            "outcome": outcome,
            "matchKind": match_kind,
            "profileVersion": (
                {
                    "kind": "document_profile",
                    "id": profile["id"],
                    "version": profile["version"],
                    "sha256": profile["contentHash"],
                }
                if profile
                else None
            ),
            "configurationVersion": (
                {
                    "kind": "configuration",
                    "id": configuration["id"],
                    "version": configuration["version"],
                }
                if configuration
                else None
            ),
            "fingerprint": {
                "kind": "document_fingerprint",
                "id": fingerprint_id,
                "version": FINGERPRINT_SPECIFICATION_VERSION,
                "sha256": fingerprint_sha,
            },
            "ledgerMatchOutcome": ledger_outcome,
            "ledgerExpenseKey": ledger_expense_key,
            "reason": reason,
            "resultHash": result_hash,
        },
        cluster=cluster_payload,
        fields=field_payloads,
        human_review_required=True,
    )
    return result.model_dump(by_alias=True, mode="json")
