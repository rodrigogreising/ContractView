from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from typing import Protocol
import uuid

from .artifacts import Artifact, read_and_verify_artifact, store_artifact
from .authorization import Actor, Role
from .ingestion import IngestionJob
from .provenance import LineageInput, append_event_tx, append_lineage_tx
from .runtime import database

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


class TesseractCliAdapter:
    provider = "tesseract-cli"
    model = "tesseract-runtime-eng"

    def extract(self, filename: str, media_type: str, content: bytes) -> OcrResponse:
        with TemporaryDirectory(prefix="contractview-ocr-") as directory:
            root = Path(directory)
            source = root / Path(filename).name
            source.write_bytes(content)
            image = source
            if media_type == "application/pdf":
                image = root / "page-1.png"
                result = subprocess.run(
                    ["pdftoppm", "-f", "1", "-singlefile", "-png", "-r", "200", str(source), str(root / "page-1")],
                    capture_output=True, text=True,
                )
                if result.returncode != 0: raise ExtractionProviderError(result.stderr.strip() or "PDF rendering failed")
            try:
                version_result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=10)
                text_result = subprocess.run(["tesseract", str(image), "stdout", "--psm", "6"], capture_output=True, text=True, timeout=30)
                tsv_result = subprocess.run(["tesseract", str(image), "stdout", "--psm", "6", "tsv"], capture_output=True, text=True, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ExtractionProviderError(f"OCR provider unavailable: {error}") from error
            if text_result.returncode != 0 or tsv_result.returncode != 0:
                raise ExtractionProviderError(text_result.stderr.strip() or tsv_result.stderr.strip() or "OCR failed")
            confidences = []
            for line in tsv_result.stdout.splitlines()[1:]:
                cells = line.split("\t")
                if len(cells) >= 12 and cells[11].strip():
                    try:
                        value = Decimal(cells[10])
                        if value >= 0: confidences.append(value)
                    except Exception: pass
            if not text_result.stdout.strip() or not confidences:
                raise InvalidExtractionResponse("OCR returned no usable text")
            confidence = (sum(confidences, Decimal("0")) / len(confidences) / Decimal("100")).quantize(Decimal("0.0001"))
            runtime_version = version_result.stdout.splitlines()[0].split(maxsplit=1)[1] if version_result.returncode == 0 else "unknown"
            return OcrResponse(self.provider, f"tesseract-{runtime_version}-eng", text_result.stdout, confidence)


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
        connection.execute(
            """insert into extraction_runs
               (id,job_id,source_artifact_id,contract_id,organization_id,provider,model,prompt_version,parser_version,schema_version,source_location,status,routing_reason,error_message)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'page=1','failed','PROVIDER_OR_RESPONSE_FAILURE',%s)""",
            (run_id,job.id,artifact.id,job.contract_id,job.organization_id,provider,model,PROMPT_VERSION,PARSER_VERSION,SCHEMA_VERSION,message),
        )
        append_event_tx(connection, "extraction_failed", "extraction_run", run_id,
                        actor_id=None, organization_id=job.organization_id, contract_id=job.contract_id,
                        payload={"artifactId": artifact.id, "error": message})
        connection.commit()


def extract_evidence(job: IngestionJob, artifact: Artifact, adapter: OcrAdapter | None = None) -> dict:
    adapter = adapter or TesseractCliAdapter()
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
        connection.execute(
            """insert into extraction_runs
               (id,job_id,source_artifact_id,raw_response_artifact_id,contract_id,organization_id,provider,model,prompt_version,parser_version,schema_version,source_location,confidence,status,routing_reason)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'needs_review',%s)""",
            (run_id,job.id,artifact.id,raw_artifact.id,job.contract_id,job.organization_id,response.provider,response.model,
             PROMPT_VERSION,PARSER_VERSION,SCHEMA_VERSION,response.source_location,response.confidence,routing),
        )
        for name, value in fields.items():
            field_id = f"field-{uuid.uuid4().hex}"
            proposed_lineage_id = append_lineage_tx(connection, LineageInput(
                job.contract_id,job.organization_id,f"{artifact.id}.{name}",value,artifact.id,response.source_location,
                extractor_provider=response.provider,extractor_model=response.model,prompt_version=PROMPT_VERSION,parser_version=PARSER_VERSION,
            ))
            connection.execute(
                "insert into extraction_fields(id,extraction_run_id,field_name,proposed_value,confidence,source_location,proposed_lineage_id) values (%s,%s,%s,%s,%s,%s,%s)",
                (field_id,run_id,name,value,response.confidence,response.source_location,proposed_lineage_id),
            )
        append_event_tx(connection,"extraction_drafted","extraction_run",run_id,organization_id=job.organization_id,
                        contract_id=job.contract_id,payload={"sourceArtifactId":artifact.id,"rawResponseArtifactId":raw_artifact.id,
                                                             "provider":response.provider,"model":response.model,"routingReason":routing})
        connection.commit()
    return {"id":run_id,"status":"needs_review","routingReason":routing,"fields":fields,"rawResponseArtifactId":raw_artifact.id}
