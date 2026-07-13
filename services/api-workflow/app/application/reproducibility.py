"""Canonical shared-contract inputs for deterministic validation and packages."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Iterable

from ..authorization import Action, Role
from ..shared_contracts import (
    ExtractionComponentVersionContract,
    PackageBuildInputContract,
    RuleDefinition,
    TemplateContract,
    ValidationInputManifestContract,
    VersionReference,
    ViewContract,
    WorkflowContract,
)


VALIDATION_MANIFEST_SCHEMA = "validation-input-manifest-v1"
PACKAGE_BUILD_SCHEMA = "package-build-input-v1"
PACKAGE_REPRODUCTION_SCHEMA = "package-reproduction-manifest-v1"
RULE_VERSIONS = {
    "SERVICE_PERIOD": "service-period-v1",
    "REQUIRED_EVIDENCE": "required-evidence-v1",
    "BUDGET_AVAILABLE": "budget-available-v1",
    "TOTAL_RECONCILIATION": "total-reconciliation-v1",
    "POSSIBLE_DUPLICATE": "possible-duplicate-v1",
}
WORKFLOW_ID = "reimbursement-review-workflow"
WORKFLOW_VERSION = 1
TEMPLATE_ID = "reimbursement-invoice-pdf"
TEMPLATE_VERSION = 1
TEMPLATE_RENDERER_VERSION = "reportlab-invoice-v1"
CLAIM_COLUMNS = [
    "expenseKey",
    "amount",
    "ledgerArtifactId",
    "ledgerSource",
    "evidenceArtifactId",
    "extractionStatus",
    "validationRunId",
    "configurationVersionId",
    "invoiceVersionId",
]


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def canonical_hash(value: object) -> str:
    return sha256(canonical_json(value).encode()).hexdigest()


def canonical_document(model: object) -> dict[str, Any]:
    return model.model_dump(by_alias=True, mode="json")  # type: ignore[attr-defined]


def rule_definitions(configuration: dict[str, Any]) -> list[RuleDefinition]:
    parameter_sources = {
        "SERVICE_PERIOD": {"servicePeriod": configuration["servicePeriod"]},
        "REQUIRED_EVIDENCE": {"requiredEvidence": configuration["requiredEvidence"]},
        "BUDGET_AVAILABLE": {"categories": configuration["categories"]},
        "TOTAL_RECONCILIATION": {
            "ledgerControlTotal": configuration["ledgerControlTotal"]
        },
        "POSSIBLE_DUPLICATE": {},
    }
    definitions = []
    for item in configuration["rules"]:
        code = item["code"]
        parameters = dict(parameter_sources[code])
        if code == "POSSIBLE_DUPLICATE":
            parameters = {
                "amountTolerance": item["amountTolerance"],
                "dayWindow": item["dayWindow"],
            }
        definitions.append(
            RuleDefinition.model_validate(
                {
                    "code": code,
                    "version": RULE_VERSIONS[code],
                    "severity": item["severity"],
                    "enabled": item["enabled"],
                    "parameters": parameters,
                }
            )
        )
    return sorted(definitions, key=lambda item: item.code.value)


def workflow_contract() -> WorkflowContract:
    return WorkflowContract.model_validate(
        {
            "id": WORKFLOW_ID,
            "version": WORKFLOW_VERSION,
            "states": ["draft", "submitted", "returned", "approved"],
            "transitions": [
                {
                    "fromState": "draft",
                    "toState": "submitted",
                    "action": Action.SUBMIT.value,
                    "role": Role.NGO_APPROVER.value,
                },
                {
                    "fromState": "submitted",
                    "toState": "returned",
                    "action": Action.RETURN.value,
                    "role": Role.GOVERNMENT_REVIEWER.value,
                },
                {
                    "fromState": "submitted",
                    "toState": "approved",
                    "action": Action.APPROVE.value,
                    "role": Role.GOVERNMENT_REVIEWER.value,
                },
            ],
        }
    )


def view_contracts() -> list[ViewContract]:
    return [
        ViewContract(
            id="ngo-approval-view",
            version=1,
            role=Role.NGO_APPROVER,
            fields=["invoice", "evidence", "validation", "attestation"],
        ),
        ViewContract(
            id="government-review-view",
            version=1,
            role=Role.GOVERNMENT_REVIEWER,
            fields=["invoice", "evidence", "validation", "package", "provenance"],
        ),
    ]


def template_contract(configuration: dict[str, Any]) -> TemplateContract:
    parameters = {
        **configuration["package"],
        "rendererVersion": TEMPLATE_RENDERER_VERSION,
        "claimColumns": CLAIM_COLUMNS,
    }
    return TemplateContract(
        id=TEMPLATE_ID,
        version=TEMPLATE_VERSION,
        media_type="application/pdf",
        content_hash=canonical_hash(parameters),
        parameters=parameters,
    )


def assert_template_integrity(template: TemplateContract) -> None:
    if canonical_hash(template.parameters or {}) != template.content_hash:
        raise ValueError("Template parameters do not match the shared contract hash")


def normalized_inputs(snapshot: dict[str, Any]) -> dict[str, Any]:
    payload = snapshot["payload"]
    return {
        "invoiceVersionId": payload["invoiceVersionId"],
        "configurationVersionId": payload["configurationVersionId"],
        "total": payload["total"],
        "lines": [
            {
                "expenseKey": line["expenseKey"],
                "date": line["expenseDate"],
                "vendor": line["vendor"],
                "category": line["budgetCategory"],
                "amount": line["claimedAmount"],
                "evidenceArtifactId": (
                    line["evidenceArtifact"]["id"] if line["evidenceArtifact"] else None
                ),
                "ledgerSource": line["ledgerSourceLocation"],
            }
            for line in payload["lines"]
        ],
    }


def _artifact_references(snapshot: dict[str, Any]) -> list[VersionReference]:
    references: dict[str, VersionReference] = {}
    for line in snapshot["payload"]["lines"]:
        for name in ("ledgerArtifact", "evidenceArtifact"):
            artifact = line[name]
            if artifact:
                references[artifact["id"]] = VersionReference(
                    kind="artifact",
                    id=artifact["id"],
                    version=1,
                    sha256=artifact["sha256"],
                )
    return [references[key] for key in sorted(references)]


def _mapping_references(snapshot: dict[str, Any]) -> list[VersionReference]:
    versions = sorted(
        {line["mappingVersion"] for line in snapshot["payload"]["lines"]}
    )
    return [VersionReference(kind="mapping", id=version, version=version) for version in versions]


def extraction_components(
    rows: Iterable[tuple[Any, ...]],
) -> list[ExtractionComponentVersionContract]:
    return [
        ExtractionComponentVersionContract(
            source_artifact=VersionReference(
                kind="artifact", id=row[0], version=1, sha256=row[1]
            ),
            raw_response_artifact=(
                VersionReference(kind="artifact", id=row[2], version=1, sha256=row[3])
                if row[2]
                else None
            ),
            provider=row[4],
            model=row[5],
            prompt_version=row[6],
            parser_version=row[7],
            schema_version=row[8],
            document_profile=(
                VersionReference(
                    kind="document_profile", id=row[9], version=row[10], sha256=row[11]
                )
                if row[9]
                else None
            ),
            configuration_version=(
                VersionReference(kind="configuration", id=row[12], version=row[13])
                if row[12]
                else None
            ),
            document_fingerprint=(
                VersionReference(
                    kind="document_fingerprint", id=row[14], version=row[15], sha256=row[16]
                )
                if row[14]
                else None
            ),
        )
        for row in rows
    ]


def validation_input_manifest(
    snapshot: dict[str, Any],
    configuration: dict[str, Any],
    extraction_rows: Iterable[tuple[Any, ...]],
    engine_version: str,
) -> ValidationInputManifestContract:
    components = extraction_components(extraction_rows)
    schema_versions = {snapshot["payload"]["schemaVersion"]} | {
        item.schema_version for item in components
    }
    return ValidationInputManifestContract(
        schema_version=VALIDATION_MANIFEST_SCHEMA,
        engine_version=engine_version,
        normalized_inputs=normalized_inputs(snapshot),
        invoice_snapshot=VersionReference(
            kind="invoice_snapshot",
            id=snapshot["id"],
            version=snapshot["payload"]["materialRevision"],
            sha256=snapshot["sha256"],
        ),
        artifacts=_artifact_references(snapshot),
        schemas=[
            VersionReference(kind="schema", id=version, version=version)
            for version in sorted(schema_versions)
        ],
        mappings=_mapping_references(snapshot),
        rules=rule_definitions(configuration),
        workflow=workflow_contract(),
        views=view_contracts(),
        templates=[template_contract(configuration)],
        configuration_version=VersionReference(
            kind="configuration",
            id=snapshot["payload"]["configurationVersionId"],
            version=configuration["version"],
            sha256=canonical_hash(configuration),
        ),
        extraction_components=components,
    )


def invoice_template_payload(snapshot_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": snapshot_payload["invoiceVersionId"],
        "version": snapshot_payload["invoiceVersion"],
        "configurationVersionId": snapshot_payload["configurationVersionId"],
        "total": snapshot_payload["total"],
        "lines": [
            {
                "expenseKey": line["expenseKey"],
                "date": line["expenseDate"],
                "vendor": line["vendor"],
                "category": line["budgetCategory"],
                "amount": line["claimedAmount"],
            }
            for line in snapshot_payload["lines"]
        ],
    }


def package_build_input(
    *,
    package_id: str,
    snapshot: dict[str, Any],
    attestation_id: str,
    validation: dict[str, Any],
    validation_input_manifest_id: str,
    validation_input_manifest_hash: str,
    configuration: dict[str, Any],
    claims: list[dict[str, Any]],
) -> PackageBuildInputContract:
    evidence: dict[str, VersionReference] = {}
    for line in snapshot["payload"]["lines"]:
        artifact = line["evidenceArtifact"]
        if artifact:
            evidence[artifact["id"]] = VersionReference(
                kind="artifact",
                id=artifact["id"],
                version=1,
                sha256=artifact["sha256"],
            )
    return PackageBuildInputContract(
        schema_version=PACKAGE_BUILD_SCHEMA,
        package_id=package_id,
        invoice_snapshot=VersionReference(
            kind="invoice_snapshot",
            id=snapshot["id"],
            version=snapshot["payload"]["materialRevision"],
            sha256=snapshot["sha256"],
        ),
        attestation_id=attestation_id,
        validation_run=VersionReference(
            kind="validation_run",
            id=validation["runId"],
            version=validation["engineVersion"],
            sha256=validation["outputHash"],
        ),
        validation_input_manifest_id=validation_input_manifest_id,
        validation_input_manifest_hash=validation_input_manifest_hash,
        configuration_version=VersionReference(
            kind="configuration",
            id=snapshot["payload"]["configurationVersionId"],
            version=configuration["version"],
            sha256=canonical_hash(configuration),
        ),
        template=template_contract(configuration),
        invoice_payload=invoice_template_payload(snapshot["payload"]),
        validation_summary=validation,
        claims=claims,
        evidence=[evidence[key] for key in sorted(evidence)],
    )
