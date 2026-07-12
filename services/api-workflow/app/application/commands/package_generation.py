from __future__ import annotations

from csv import DictWriter
from hashlib import sha256
from io import BytesIO, StringIO
import json
import uuid
import zipfile

from .access_scope import invoice_scope
from .artifacts import download_artifact, store_artifact
from .attestation import current_attestation
from .invoice_snapshots import create_invoice_snapshot_tx
from .provenance import append_event_tx, append_relation_tx
from ..package_rendering import render_invoice_pdf
from ..ports.statements import Statement
from ..reproducibility import (
    CLAIM_COLUMNS,
    PACKAGE_REPRODUCTION_SCHEMA,
    canonical_document,
    canonical_hash,
    package_build_input,
)
from ..transaction import transaction as database
from ...authorization import Action, Actor, ResourceKind, execute_authorized, require_permission
from ...shared_contracts import (
    PackageBuildInputContract,
    PackageFileDigestContract,
    PackageReproductionManifestContract,
)


class PackageError(ValueError):
    pass


def _json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def _claims(snapshot: dict, validation: dict) -> list[dict]:
    payload = snapshot["payload"]
    return [
        {
            "expenseKey": line["expenseKey"],
            "amount": line["claimedAmount"],
            "ledgerArtifactId": line["ledgerArtifact"]["id"],
            "ledgerSource": line["ledgerSourceLocation"],
            "evidenceArtifactId": (
                line["evidenceArtifact"]["id"] if line["evidenceArtifact"] else None
            ),
            "extractionStatus": line["extractionStatus"],
            "validationRunId": validation["runId"],
            "configurationVersionId": payload["configurationVersionId"],
            "invoiceVersionId": payload["invoiceVersionId"],
        }
        for line in payload["lines"]
    ]


def _evidence_bytes(actor: Actor, build_input: PackageBuildInputContract) -> dict[str, bytes]:
    evidence: dict[str, bytes] = {}
    for reference in build_input.evidence:
        content = download_artifact(actor, reference.id)
        if sha256(content).hexdigest() != reference.sha256:
            raise PackageError(f"Evidence artifact hash mismatch: {reference.id}")
        evidence[reference.id] = content
    return evidence


def _package_content(
    actor: Actor,
    build_input: PackageBuildInputContract,
) -> tuple[dict[str, bytes], dict, bytes]:
    claims = build_input.claims
    csv_output = StringIO()
    writer = DictWriter(csv_output, fieldnames=CLAIM_COLUMNS)
    writer.writeheader()
    writer.writerows(claims)
    files = {
        "invoice.pdf": render_invoice_pdf(build_input.invoice_payload, build_input.template),
        "validation-summary.json": _json(build_input.validation_summary),
        "manifest.csv": csv_output.getvalue().encode(),
    }
    for artifact_id, content in sorted(_evidence_bytes(actor, build_input).items()):
        files[f"evidence/{artifact_id}"] = content
    manifest = {
        "schemaVersion": build_input.schema_version,
        "packageId": build_input.package_id,
        "invoiceSnapshot": canonical_document(build_input.invoice_snapshot),
        "attestationId": build_input.attestation_id,
        "validationRun": canonical_document(build_input.validation_run),
        "validationInputManifestId": build_input.validation_input_manifest_id,
        "validationInputManifestHash": build_input.validation_input_manifest_hash,
        "configurationVersion": canonical_document(build_input.configuration_version),
        "template": canonical_document(build_input.template),
        "claims": claims,
        "files": [
            {"path": path, "sha256": sha256(content).hexdigest(), "byteSize": len(content)}
            for path, content in sorted(files.items())
        ],
    }
    files["manifest.json"] = _json(manifest)
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_STORED) as package_zip:
        for path, content in sorted(files.items()):
            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            package_zip.writestr(info, content)
    return files, manifest, archive.getvalue()


def _reproduction_manifest(
    build_input: PackageBuildInputContract,
    files: dict[str, bytes],
    manifest: dict,
    archive: bytes,
) -> PackageReproductionManifestContract:
    return PackageReproductionManifestContract(
        schema_version=PACKAGE_REPRODUCTION_SCHEMA,
        build_input_hash=canonical_hash(canonical_document(build_input)),
        package_manifest_hash=canonical_hash(manifest),
        archive_sha256=sha256(archive).hexdigest(),
        archive_byte_size=len(archive),
        files=[
            PackageFileDigestContract(
                path=path,
                sha256=sha256(content).hexdigest(),
                byte_size=len(content),
            )
            for path, content in sorted(files.items())
        ],
        template=build_input.template,
        validation_input_manifest_id=build_input.validation_input_manifest_id,
        validation_input_manifest_hash=build_input.validation_input_manifest_hash,
        invoice_snapshot=build_input.invoice_snapshot,
    )


def generate_package(actor: Actor, invoice_id: str) -> dict:
    with database() as connection:
        row = connection.invoices.execute(
            Statement.PACKAGE_GENERATION_READ_INVOICE_VERSIONS_001, (invoice_id,)
        ).fetchone()
    if not row:
        raise FileNotFoundError(invoice_id)
    scope = invoice_scope(actor, invoice_id, kind=ResourceKind.PACKAGE)

    def command():
        attestation = current_attestation(actor, invoice_id)
        if not attestation or not attestation["current"]:
            raise PackageError("A current exact-version attestation is required")
        package_id = f"package-{uuid.uuid4().hex}"
        reproduction_id = f"package-reproduction-{package_id}"
        with database() as connection:
            run = connection.validation.execute(
                Statement.PACKAGE_GENERATION_READ_VALIDATION_RUNS_002,
                (attestation["validationRunId"],),
            ).fetchone()
            if not run:
                raise PackageError("Attested validation evidence is missing")
            snapshot = create_invoice_snapshot_tx(connection, actor, invoice_id, "package")
            configuration_row = connection.configuration.execute(
                Statement.PACKAGE_GENERATION_READ_CONFIGURATION_VERSIONS_005,
                (snapshot["payload"]["configurationVersionId"],),
            ).fetchone()
            if not configuration_row:
                raise PackageError("Invoice configuration version is missing")
            validation = {
                "runId": run[0],
                "engineVersion": run[1],
                "inputHash": run[2],
                "outputHash": run[3],
            }
            build_input = package_build_input(
                package_id=package_id,
                snapshot=snapshot,
                attestation_id=attestation["id"],
                validation=validation,
                validation_input_manifest_id=run[4],
                validation_input_manifest_hash=run[5],
                configuration=configuration_row[0],
                claims=_claims(snapshot, validation),
            )
            files, manifest, archive = _package_content(actor, build_input)
            reproduction = _reproduction_manifest(build_input, files, manifest, archive)
            build_document = canonical_document(build_input)
            reproduction_document = canonical_document(reproduction)

            stored = {
                path: store_artifact(
                    actor,
                    row[1],
                    path.split("/")[-1],
                    (
                        "application/pdf"
                        if path.endswith(".pdf")
                        else "application/json"
                        if path.endswith(".json")
                        else "text/csv"
                        if path.endswith(".csv")
                        else "application/octet-stream"
                    ),
                    content,
                    artifact_kind="generated",
                )
                for path, content in files.items()
            }
            zip_artifact = store_artifact(
                actor,
                row[1],
                f"invoice-v{snapshot['payload']['invoiceVersion']}-package.zip",
                "application/zip",
                archive,
                artifact_kind="generated",
            )
            connection.packages.execute(
                Statement.PACKAGE_GENERATION_WRITE_PACKAGES_003,
                (
                    package_id,
                    invoice_id,
                    attestation["id"],
                    snapshot["payload"]["invoiceVersion"],
                    zip_artifact.id,
                    json.dumps(manifest),
                    actor.user_id,
                    snapshot["id"],
                ),
            )
            append_relation_tx(
                connection,
                row[1],
                row[0],
                "derived_from",
                {
                    "kind": "package",
                    "id": package_id,
                    "version": snapshot["payload"]["invoiceVersion"],
                },
                canonical_document(build_input.invoice_snapshot),
                actor=actor,
            )
            for path, artifact in stored.items():
                connection.packages.execute(
                    Statement.PACKAGE_GENERATION_WRITE_PACKAGE_ARTIFACTS_004,
                    (package_id, artifact.id, path, artifact.sha256),
                )
            connection.packages.execute(
                Statement.PACKAGE_GENERATION_WRITE_PACKAGE_ARTIFACTS_004,
                (package_id, zip_artifact.id, "package.zip", zip_artifact.sha256),
            )
            connection.packages.execute(
                Statement.PACKAGE_GENERATION_WRITE_PACKAGE_REPRODUCTION_MANIFESTS_008,
                (
                    reproduction_id,
                    package_id,
                    run[4],
                    snapshot["id"],
                    build_input.template.id,
                    build_input.template.version,
                    build_input.template.content_hash,
                    json.dumps(build_document),
                    reproduction.build_input_hash,
                    json.dumps(reproduction_document),
                    canonical_hash(reproduction_document),
                    reproduction.package_manifest_hash,
                    reproduction.archive_sha256,
                    reproduction.archive_byte_size,
                ),
            )
            append_event_tx(
                connection,
                "package_generated",
                "package",
                package_id,
                actor_id=actor.user_id,
                organization_id=row[0],
                contract_id=row[1],
                payload={
                    "invoiceVersionId": invoice_id,
                    "zipArtifactId": zip_artifact.id,
                    "zipSha256": zip_artifact.sha256,
                    "invoiceSnapshotId": snapshot["id"],
                    "validationInputManifestId": run[4],
                    "validationInputManifestHash": run[5],
                    "reproductionManifestId": reproduction_id,
                    "reproductionManifestHash": canonical_hash(reproduction_document),
                },
                version_references=[
                    {
                        "kind": "package",
                        "id": package_id,
                        "version": snapshot["payload"]["invoiceVersion"],
                    },
                    canonical_document(build_input.invoice_snapshot),
                    {
                        "kind": "package_manifest",
                        "id": reproduction_id,
                        "version": reproduction.schema_version,
                        "sha256": canonical_hash(reproduction_document),
                    },
                    {
                        "kind": "artifact",
                        "id": zip_artifact.id,
                        "version": 1,
                        "sha256": zip_artifact.sha256,
                    },
                ],
            )
            connection.commit()
        return {
            "id": package_id,
            "invoiceVersionId": invoice_id,
            "manifest": manifest,
            "artifacts": {
                path: {"id": artifact.id, "sha256": artifact.sha256}
                for path, artifact in stored.items()
            },
            "zip": {"id": zip_artifact.id, "sha256": zip_artifact.sha256},
            "reproduction": {
                "id": reproduction_id,
                "inputHash": reproduction.build_input_hash,
                "manifestHash": canonical_hash(reproduction_document),
                **reproduction_document,
            },
        }

    return execute_authorized(actor, Action.SUBMIT, scope, command)


def reproduce_package(actor: Actor, package_id: str) -> dict:
    with database() as connection:
        package = connection.packages.execute(
            Statement.PACKAGE_GENERATION_READ_PACKAGES_009, (package_id,)
        ).fetchone()
    if not package:
        raise FileNotFoundError(package_id)
    require_permission(
        actor,
        Action.READ,
        invoice_scope(actor, package[0], kind=ResourceKind.PACKAGE),
    )
    with database() as connection:
        row = connection.packages.execute(
            Statement.PACKAGE_GENERATION_READ_PACKAGE_REPRODUCTION_MANIFESTS_007,
            (package_id,),
        ).fetchone()
    if not row:
        raise PackageError("Package predates reproduction manifests")
    build_input = PackageBuildInputContract.model_validate(row[0])
    persisted_reproduction = PackageReproductionManifestContract.model_validate(row[2])
    files, manifest, archive = _package_content(actor, build_input)
    reproduced = _reproduction_manifest(build_input, files, manifest, archive)
    reproduced_document = canonical_document(reproduced)
    reproduction_hash = canonical_hash(reproduced_document)
    persisted_files = {item.path: item.sha256 for item in persisted_reproduction.files}
    reproduced_files = {item.path: item.sha256 for item in reproduced.files}
    checks = {
        "buildInputHash": canonical_hash(canonical_document(build_input)) == row[1],
        "reproductionManifest": reproduced == persisted_reproduction,
        "reproductionManifestHash": reproduction_hash == row[3],
        "packageManifestHash": reproduced.package_manifest_hash == row[4],
        "archiveSha256": reproduced.archive_sha256 == row[5],
        "archiveByteSize": reproduced.archive_byte_size == row[6],
    }
    return {
        "packageId": package_id,
        "matches": all(checks.values()),
        "checks": checks,
        "fileChecks": {
            path: reproduced_files.get(path) == digest
            for path, digest in persisted_files.items()
        },
        "buildInputHash": reproduced.build_input_hash,
        "packageManifestHash": reproduced.package_manifest_hash,
        "archiveSha256": reproduced.archive_sha256,
        "archiveByteSize": reproduced.archive_byte_size,
        "archiveBytes": archive,
        "manifest": manifest,
        "reproductionManifestHash": reproduction_hash,
    }
