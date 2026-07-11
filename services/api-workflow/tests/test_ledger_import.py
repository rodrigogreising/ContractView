from decimal import Decimal
from pathlib import Path

from app.authorization import Actor, Role
from app.configuration import activate_draft
from app.ingestion import claim_next_job, create_upload_job, list_jobs, process_job
from app.ledger_import import parse_ledger
from app.runtime import database

CONTRACT = "contract-metro-harbor-2026"
PREPARER = Actor("user-ngo-preparer", "org-ngo", Role.NGO_PREPARER)
ADMIN = Actor("user-config-admin", "org-operations", Role.CONFIGURATION_ADMINISTRATOR)
FILES = Path("/app/fixtures/files")


def ensure_active():
    with database() as connection:
        exists = connection.execute("select 1 from configuration_versions where contract_id=%s limit 1", (CONTRACT,)).fetchone()
    if not exists:
        activate_draft(ADMIN, CONTRACT)


def test_golden_csv_and_xlsx_parse_to_identical_canonical_rows_and_total():
    csv_sheet, csv_rows = parse_ledger("ledger.csv", (FILES / "ledger-june-2026.csv").read_bytes())
    xlsx_sheet, xlsx_rows = parse_ledger("ledger.xlsx", (FILES / "ledger-june-2026.xlsx").read_bytes())
    assert csv_sheet == "CSV" and xlsx_sheet == "June Ledger"
    assert [row[1] for row in csv_rows] == [row[1] for row in xlsx_rows]
    assert len(csv_rows) == 5
    assert sum((row[1]["amount"] for row in csv_rows), Decimal("0.00")) == Decimal("10130.00")


def test_worker_import_persists_rows_versions_cells_lineage_and_reconciliation():
    ensure_active()
    job = create_upload_job(PREPARER, CONTRACT, "golden-ledger.csv", "text/csv", (FILES / "ledger-june-2026.csv").read_bytes())
    claimed = claim_next_job(); assert claimed and claimed.id == job.id
    process_job(claimed)
    assert {item.id:item for item in list_jobs(PREPARER, CONTRACT)}[job.id].status == "completed"
    with database() as connection:
        summary = connection.execute(
            "select row_count,control_total,imported_total,importer_version,schema_version,mapping_version from ledger_imports where job_id=%s", (job.id,)
        ).fetchone()
        expense = connection.execute(
            "select expense_key,amount,source_sheet,source_row,source_cells->>'amount',importer_version,schema_version,mapping_version from expense_rows where ledger_import_id=(select id from ledger_imports where job_id=%s) and expense_key='EXP-003'", (job.id,)
        ).fetchone()
        lineage = connection.execute(
            "select field_value,source_location,importer_version,mapping_version from field_lineage where field_name='EXP-003.amount' order by id desc limit 1"
        ).fetchone()
    assert summary[:3] == (5, Decimal("10130.00"), Decimal("10130.00"))
    assert summary[3:] == ("ledger-importer-v1", "expense-row-v1", "poc-ledger-mapping-v1")
    assert expense == ("EXP-003", Decimal("1280.00"), "CSV", 4, "F4", "ledger-importer-v1", "expense-row-v1", "poc-ledger-mapping-v1")
    assert lineage == ("1280.00", "CSV!F4", "ledger-importer-v1", "poc-ledger-mapping-v1")


def test_malformed_and_unreconciled_ledgers_fail_without_partial_rows():
    ensure_active()
    malformed = b"bad,headers\nvalue,1\n"
    source = (FILES / "ledger-june-2026.csv").read_text().replace("4200.00", "4200.01").encode()
    for filename, content in (("malformed-ledger.csv", malformed), ("unreconciled-ledger.csv", source)):
        job = create_upload_job(PREPARER, CONTRACT, filename, "text/csv", content)
        claimed = claim_next_job(); assert claimed and claimed.id == job.id
        process_job(claimed)
        failed = {item.id:item for item in list_jobs(PREPARER, CONTRACT)}[job.id]
        assert failed.status == "failed" and failed.error_message
        with database() as connection:
            rows = connection.execute("select count(*) from expense_rows where source_artifact_id=%s", (job.artifact_id,)).fetchone()[0]
        assert rows == 0
