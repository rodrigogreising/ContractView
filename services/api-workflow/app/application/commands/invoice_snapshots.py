from hashlib import sha256
import json
import uuid

from ...authorization import Actor
from ..ports.statements import Statement


SNAPSHOT_SCHEMA_VERSION = "invoice-snapshot-v1"


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def create_invoice_snapshot_tx(connection, actor: Actor, invoice_id: str, stage: str) -> dict:
    invoice = connection.invoices.execute(
        Statement.INVOICE_SNAPSHOTS_READ_INVOICE_VERSIONS_002,
        (invoice_id,),
    ).fetchone()
    if not invoice:
        raise FileNotFoundError(invoice_id)
    existing = connection.invoices.execute(
        Statement.INVOICE_SNAPSHOTS_READ_INVOICE_SNAPSHOTS_001,
        (invoice_id, invoice[3], stage),
    ).fetchone()
    if existing:
        return {"id": existing[0], "payload": existing[1], "sha256": existing[2]}
    rows = connection.read_models.execute(
        Statement.INVOICE_SNAPSHOTS_READ_ARTIFACTS_INVOICE_LINES_003,
        (invoice_id,),
    ).fetchall()
    payload = {
        "schemaVersion": SNAPSHOT_SCHEMA_VERSION,
        "invoiceVersionId": invoice_id,
        "contractId": invoice[0],
        "organizationId": invoice[1],
        "invoiceVersion": invoice[2],
        "materialRevision": invoice[3],
        "configurationVersionId": invoice[4],
        "lifecycleState": invoice[5],
        "total": f"{invoice[6]:.2f}",
        "lines": [
            {
                "expenseKey": row[0],
                "expenseDate": row[1].isoformat(),
                "vendor": row[2],
                "description": row[3],
                "budgetCategory": row[4],
                "claimedAmount": f"{row[5]:.2f}",
                "ledgerArtifact": {"id": row[6], "sha256": row[7]},
                "ledgerSourceLocation": row[8],
                "evidenceArtifact": (
                    {"id": row[9], "sha256": row[10]} if row[9] else None
                ),
                "extractionStatus": row[11],
                "mappingVersion": row[12],
            }
            for row in rows
        ],
    }
    digest = sha256(_canonical(payload).encode()).hexdigest()
    snapshot_id = f"invoice-snapshot-{uuid.uuid4().hex}"
    connection.invoices.execute(
        Statement.INVOICE_SNAPSHOTS_WRITE_INVOICE_SNAPSHOTS_004,
        (
            snapshot_id,
            invoice_id,
            invoice[0],
            invoice[1],
            invoice[2],
            invoice[3],
            stage,
            json.dumps(payload),
            digest,
            actor.user_id,
            actor.role.value,
        ),
    )
    return {"id": snapshot_id, "payload": payload, "sha256": digest}
