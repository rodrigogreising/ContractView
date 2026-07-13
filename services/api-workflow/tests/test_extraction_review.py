from decimal import Decimal

import psycopg
import pytest
import uuid

from app.authorization import Actor, ForbiddenError, Role
from app.extraction import OcrResponse
from app.extraction_review import InvalidReview, UnreviewedField, list_extractions, review_field, reviewed_value
from app.ingestion import claim_next_job, create_upload_job, process_job
from app.runtime import database
from configuration_helpers import ensure_active_configuration

CONTRACT = "contract-synthetic-agency-ngo-2026"
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
APPROVER = Actor("user-ngo-approver", "org-ngo", Role.NGO_APPROVER)
OTHER_NGO = Actor("outside-user", "org-outside", Role.NGO_PREPARER)
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
TEXT = """Synthetic Program Supplies Vendor B
Test fixture only - no real organization, person, account, or transaction.
Invoice: SYN-SUP-0618
Date: 2026-06-18
VENDOR INVOICE
Description: Workshop materials and learning kits
Amount: $1,820.00
Printed subtotal: $1,820.00
Approved adjustment: $-540.00
Approved claim total: $1,280.00
APPROVAL NOTE
Claim only the approved adjusted total; exclude the non-program materials adjustment.
Expense reference: VENDOR-INVOICE-EXP-003
"""


@pytest.fixture(scope="module", autouse=True)
def active_profile_configuration():
    return ensure_active_configuration(ADMIN, CONTRACT)


class ReviewFixtureAdapter:
    provider = "review-fixture-provider"
    model = "review-fixture-model-v1"
    def extract(self, filename, media_type, content):
        return OcrResponse(self.provider,self.model,TEXT,Decimal("0.9500"))


def create_proposals():
    marker = uuid.uuid4().hex
    filename = f"review-exp-003-{marker}.pdf"
    job = create_upload_job(PREPARER, CONTRACT, filename, "application/pdf", f"synthetic-review-source-{marker}".encode())
    claimed = claim_next_job(); assert claimed and claimed.id == job.id
    process_job(claimed, ReviewFixtureAdapter())
    queue = list_extractions(PREPARER, CONTRACT)
    return next(item for item in queue if item["filename"] == filename)


def test_preparer_corrects_amount_and_accepts_other_fields_with_complete_history():
    extraction = create_proposals()
    fields = {field["name"]:field for field in extraction["fields"]}
    with pytest.raises(UnreviewedField): reviewed_value(fields["amount"]["id"])
    corrected = review_field(PREPARER, fields["amount"]["id"], "correct", "1280.00", "Approved claim total on source")
    assert corrected["proposedValue"] == "1820.00" and corrected["reviewedValue"] == "1280.00"
    for name in ("vendor","date","sourceReference"):
        review_field(PREPARER, fields[name]["id"], "accept", fields[name]["proposedValue"], "Matched source evidence")
    assert reviewed_value(fields["amount"]["id"]) == "1280.00"
    with database() as connection:
        review = connection.execute(
            """select decision,proposed_value,reviewed_value,actor_id,reason,source_artifact_id,
                      source_location,created_at is not null,predecessor_lineage_id,reviewed_lineage_id
               from extraction_field_reviews where extraction_field_id=%s""", (fields["amount"]["id"],)
        ).fetchone()
        lineages = connection.execute(
            "select field_value,predecessor_lineage_id from field_lineage where id in (%s,%s) order by id",
            (review[8],review[9]),
        ).fetchall()
        event = connection.execute(
            "select event_type,payload->>'decision',payload->>'proposedValue',payload->>'reviewedValue' from domain_events where aggregate_id=%s",
            (fields["amount"]["id"],),
        ).fetchone()
    assert review[:8] == ("correct","1820.00","1280.00",PREPARER.user_id,"Approved claim total on source",extraction["sourceArtifactId"],"page=1;line=7;label=amount",True)
    assert lineages == [("1820.00",None),("1280.00",review[8])]
    assert event == ("field_corrected","correct","1820.00","1280.00")


def test_authority_and_single_review_guards_create_no_extra_history():
    extraction = create_proposals()
    amount = next(field for field in extraction["fields"] if field["name"] == "amount")
    for actor in (APPROVER,OTHER_NGO):
        with pytest.raises(ForbiddenError): review_field(actor,amount["id"],"correct","1280.00")
    with database() as connection:
        assert connection.execute("select count(*) from extraction_field_reviews where extraction_field_id=%s",(amount["id"],)).fetchone()[0] == 0
    with pytest.raises(InvalidReview,match="different"): review_field(PREPARER,amount["id"],"correct","1820.00")
    review_field(PREPARER,amount["id"],"correct","1280.00")
    with pytest.raises(InvalidReview,match="already"): review_field(PREPARER,amount["id"],"correct","1200.00")
    with database() as connection:
        review_id = connection.execute("select id from extraction_field_reviews where extraction_field_id=%s",(amount["id"],)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException,match="append-only"):
        with database() as connection: connection.execute("delete from extraction_field_reviews where id=%s",(review_id,))
