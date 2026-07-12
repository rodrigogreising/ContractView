from decimal import Decimal
from pathlib import Path
import json

import pytest

from app.artifacts import store_artifact
from app.authorization import Actor, ForbiddenError, Role
from app.configuration import update_draft
from configuration_helpers import ensure_active_configuration
from app.extraction import OcrResponse
from app.extraction_review import list_extractions, review_field
from app.ingestion import claim_next_job, create_upload_job, process_job
from app.invoice_draft import assemble_draft
from app.runtime import database

CONTRACT="contract-synthetic-agency-ngo-2026"
PREPARER=Actor("user-ngo-preparer","org-ngo",Role.NGO_PREPARER)
APPROVER=Actor("user-ngo-approver","org-ngo",Role.NGO_APPROVER)
ADMIN=Actor("user-config-admin","org-operations",Role.CONFIGURATION_ADMINISTRATOR)
FILES=Path("/app/fixtures/files")

class InvoiceAdapter:
    provider="invoice-fixture-provider"; model="invoice-fixture-model-v1"
    def extract(self,*_): return OcrResponse(self.provider,self.model,"Synthetic Program Supplies Vendor B\nDate: 2026-06-18\nWorkshop materials and learning kits $1,820.00\nExpense reference: VENDOR-INVOICE-EXP-003\n",Decimal("0.9500"))

def complete_job(job,adapter=None):
    claimed=claim_next_job(); assert claimed and claimed.id==job.id
    process_job(claimed,adapter)

@pytest.fixture(scope="module",autouse=True)
def setup_complete_sources():
    update_draft(ADMIN,CONTRACT,json.loads(Path("/app/fixtures/scenario.json").read_text())["initialConfiguration"])
    ensure_active_configuration(ADMIN,CONTRACT)
    ledger=create_upload_job(PREPARER,CONTRACT,"assembly-ledger.csv","text/csv",(FILES/"ledger-june-2026.csv").read_bytes()); complete_job(ledger)
    for filename in ("payroll-june-2026.xlsx","vendor-invoice-exp-002.pdf","vendor-invoice-exp-004.png","vendor-invoice-exp-005.pdf"):
        path=FILES/filename
        media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filename.endswith(".xlsx") else "image/png" if filename.endswith(".png") else "application/pdf"
        store_artifact(PREPARER,CONTRACT,filename,media,path.read_bytes())
    extraction_job=create_upload_job(PREPARER,CONTRACT,"vendor-invoice-exp-003.pdf","application/pdf",(FILES/"vendor-invoice-exp-003.pdf").read_bytes()); complete_job(extraction_job,InvoiceAdapter())
    extraction=next(item for item in list_extractions(PREPARER,CONTRACT) if item["filename"]=="vendor-invoice-exp-003.pdf")
    amount=next(field for field in extraction["fields"] if field["name"]=="amount")
    review_field(PREPARER,amount["id"],"correct","1280.00","Approved claim total")

def test_assembles_evidence_linked_decimal_draft_with_stable_version_and_totals():
    draft=assemble_draft(PREPARER,CONTRACT)
    repeated=assemble_draft(PREPARER,CONTRACT)
    assert repeated["id"]==draft["id"] and repeated["version"]==draft["version"]
    assert draft["total"]=="10130.00" and draft["findings"]==[] and len(draft["lines"])==5
    categories={item["name"]:item for item in draft["categories"]}
    assert categories=={
        "Personnel":{"name":"Personnel","claimed":"4200.00","limit":"60000.00","available":"55800.00"},
        "Facilities":{"name":"Facilities","claimed":"3700.00","limit":"24000.00","available":"20300.00"},
        "Program Supplies":{"name":"Program Supplies","claimed":"2230.00","limit":"12000.00","available":"9770.00"},
    }
    exp3=next(line for line in draft["lines"] if line["expenseKey"]=="EXP-003")
    assert exp3["amount"]=="1280.00" and exp3["ledgerSource"]=="CSV!F4" and exp3["evidenceArtifactId"] and exp3["extractionStatus"]=="corrected"
    assert all(line["ledgerArtifactId"] and line["evidenceArtifactId"] for line in draft["lines"])
    with database() as connection:
        lineage=connection.execute("select field_value,invoice_version_id,source_location from field_lineage where invoice_version_id=%s and field_name='EXP-003.claimedAmount'",(draft["id"],)).fetchone()
    assert lineage==("1280.00",draft["id"],"CSV!F4")

def test_missing_evidence_is_visible_and_non_preparer_cannot_assemble():
    with pytest.raises(ForbiddenError): assemble_draft(APPROVER,CONTRACT)
    source=(FILES/"ledger-june-2026.csv").read_text().replace("vendor-invoice-exp-005.pdf","missing-exp-005.pdf").encode()
    ledger=create_upload_job(PREPARER,CONTRACT,"assembly-missing-ledger.csv","text/csv",source); complete_job(ledger)
    draft=assemble_draft(PREPARER,CONTRACT)
    assert any(item["code"]=="MISSING_EVIDENCE" and item["expenseKey"]=="EXP-005" for item in draft["findings"])
    assert next(line for line in draft["lines"] if line["expenseKey"]=="EXP-005")["extractionStatus"]=="missing"
