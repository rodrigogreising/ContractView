from dataclasses import dataclass
from decimal import Decimal
import json
import re
from typing import Protocol
import uuid

from .artifacts import Artifact, read_and_verify_artifact, store_artifact
from ...authorization import Actor, Role
from .ingestion import IngestionJob
from .provenance import LineageInput, append_event_tx, append_lineage_tx

from ..ports.statements import Statement
from ..transaction import transaction as database
from ..extraction_provider import extraction_adapter
PROMPT_VERSION = "vendor-invoice-fields-v1"
PARSER_VERSION = "vendor-invoice-parser-v1"
SCHEMA_VERSION = "vendor-date-amount-reference-v1"
REVIEW_THRESHOLD = Decimal("0.8500")


class ExtractionProviderError(RuntimeError): pass
class InvalidExtractionResponse(ValueError): pass


@dataclass(frozen=True)
class OcrResponse:
    provider: str
    model: str
    text: str
    confidence: Decimal
    source_location: str = "page=1"


class OcrAdapter(Protocol):
    def extract(self, filename: str, media_type: str, content: bytes) -> OcrResponse: ...


def parse_vendor_invoice(response: OcrResponse) -> dict[str, str]:
    lines = [line.strip() for line in response.text.splitlines() if line.strip()]
    vendor = next((line for line in lines if len(line) >= 4 and not line.lower().startswith((
        "synthetic", "vendor invoice", "date:", "description", "workshop", "printed", "approved",
        "claim only", "expense reference", "no real",
    ))), None)
    date_match = re.search(r"\bDate:\s*(\d{4}-\d{2}-\d{2})", response.text, re.I)
    amount_match = re.search(r"Workshop materials[^$]*\$\s*([\d,]+\.\d{2})", response.text, re.I)
    reference_match = re.search(r"Expense reference:\s*([A-Z0-9-]+)", response.text, re.I)
    if not vendor or not date_match or not amount_match or not reference_match:
        raise InvalidExtractionResponse("OCR response does not match vendor-date-amount-reference-v1")
    return {
        "vendor": vendor,
        "date": date_match.group(1),
        "amount": amount_match.group(1).replace(",", ""),
        "sourceReference": reference_match.group(1),
    }


def _record_failure(job: IngestionJob, artifact: Artifact, provider: str, model: str, message: str) -> None:
    run_id = f"extraction-{uuid.uuid4().hex}"
    with database() as connection:
        connection.extraction.execute(Statement.EXTRACTION_WRITE_EXTRACTION_RUNS_001,
            (run_id,job.id,artifact.id,job.contract_id,job.organization_id,provider,model,PROMPT_VERSION,PARSER_VERSION,SCHEMA_VERSION,message),
        )
        append_event_tx(connection, "extraction_failed", "extraction_run", run_id,
                        actor_id=None, organization_id=job.organization_id, contract_id=job.contract_id,
                        payload={"artifactId": artifact.id, "error": message})
        connection.commit()


def extract_evidence(job: IngestionJob, artifact: Artifact, adapter: OcrAdapter | None = None) -> dict:
    adapter = adapter or extraction_adapter()
    content = read_and_verify_artifact(artifact)
    try:
        response = adapter.extract(artifact.filename, artifact.media_type, content)
        fields = parse_vendor_invoice(response)
    except Exception as error:
        _record_failure(job, artifact, getattr(adapter, "provider", "unknown"), getattr(adapter, "model", "unknown"), str(error))
        raise
    raw = json.dumps({
        "provider": response.provider, "model": response.model, "text": response.text,
        "confidence": str(response.confidence), "sourceLocation": response.source_location,
        "promptVersion": PROMPT_VERSION, "parserVersion": PARSER_VERSION,
    }, sort_keys=True).encode()
    actor = Actor(artifact.created_by, artifact.organization_id, Role.NGO_PREPARER)
    raw_artifact = store_artifact(actor, artifact.contract_id, f"{artifact.id}-ocr-response.json", "application/json", raw,
                                  artifact_kind="generated", predecessor_id=artifact.id, relation_type="derived_from")
    run_id = f"extraction-{uuid.uuid4().hex}"
    routing = "LOW_CONFIDENCE" if response.confidence < REVIEW_THRESHOLD else "HUMAN_REVIEW_REQUIRED"
    with database() as connection:
        connection.extraction.execute(Statement.EXTRACTION_WRITE_EXTRACTION_RUNS_002,
            (run_id,job.id,artifact.id,raw_artifact.id,job.contract_id,job.organization_id,response.provider,response.model,
             PROMPT_VERSION,PARSER_VERSION,SCHEMA_VERSION,response.source_location,response.confidence,routing),
        )
        for name, value in fields.items():
            field_id = f"field-{uuid.uuid4().hex}"
            proposed_lineage_id = append_lineage_tx(connection, LineageInput(
                job.contract_id,job.organization_id,f"{artifact.id}.{name}",value,artifact.id,response.source_location,
                extractor_provider=response.provider,extractor_model=response.model,prompt_version=PROMPT_VERSION,parser_version=PARSER_VERSION,
            ))
            connection.extraction.execute(Statement.EXTRACTION_WRITE_EXTRACTION_FIELDS_003,
                (field_id,run_id,name,value,response.confidence,response.source_location,proposed_lineage_id),
            )
        append_event_tx(connection,"extraction_drafted","extraction_run",run_id,organization_id=job.organization_id,
                        contract_id=job.contract_id,payload={"sourceArtifactId":artifact.id,"rawResponseArtifactId":raw_artifact.id,
                                                             "provider":response.provider,"model":response.model,"routingReason":routing})
        connection.commit()
    return {"id":run_id,"status":"needs_review","routingReason":routing,"fields":fields,"rawResponseArtifactId":raw_artifact.id}
