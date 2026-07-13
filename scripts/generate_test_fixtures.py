"""Generate the complete deterministic synthetic fixture pack from scenario.json."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = ROOT / "services" / "api-workflow"
if SERVICE_ROOT.exists():
    sys.path.insert(0, str(SERVICE_ROOT))

from app.domain.document_intake import (  # noqa: E402
    EVALUATION_SUITE_VERSION,
    FINGERPRINT_SPECIFICATION_VERSION,
    PARSER_VERSION as PROFILE_PARSER_VERSION,
    analyze_profile,
    content_hash,
    evaluate_profile,
)


FIXED_TIME = datetime(2000, 1, 1, tzinfo=timezone.utc)
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
GENERATOR = "Synthetic Fixture Generator"
LEDGER_FIELDS = (
    "expense_id",
    "expense_date",
    "vendor",
    "description",
    "budget_category",
    "amount",
    "invoice_number",
    "evidence_file",
)


def money(value: str) -> str:
    return f"${Decimal(value):,.2f}"


def normalize_xlsx(path: Path) -> None:
    source = path.read_bytes()
    entries: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(source), "r") as archive:
        for name in sorted(archive.namelist()):
            content = archive.read(name)
            if name == "docProps/core.xml":
                content = re.sub(
                    rb"(<dcterms:modified[^>]*>)[^<]+",
                    rb"\g<1>2000-01-01T00:00:00Z",
                    content,
                )
            entries.append((name, content))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in entries:
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o600 << 16
            archive.writestr(info, content)
    path.write_bytes(buffer.getvalue())


def workbook(path: Path, sheet_name: str, headers: tuple[str, ...], rows: list[dict]) -> None:
    book = Workbook()
    sheet = book.active
    sheet.title = sheet_name
    sheet.append(list(headers))
    for row in rows:
        sheet.append([row[header] for header in headers])
    book.properties.creator = GENERATOR
    book.properties.lastModifiedBy = GENERATOR
    book.properties.title = "Synthetic test fixture"
    book.properties.subject = "No real organization or personal data"
    book.properties.created = FIXED_TIME.replace(tzinfo=None)
    book.properties.modified = FIXED_TIME.replace(tzinfo=None)
    book.save(path)
    normalize_xlsx(path)


def vendor_pdf(path: Path, invoice: dict[str, str]) -> None:
    document = canvas.Canvas(
        str(path), pagesize=letter, pageCompression=1, invariant=1
    )
    document.setAuthor(GENERATOR)
    document.setCreator(GENERATOR)
    document.setTitle("Synthetic vendor invoice")
    document.setSubject("Test fixture containing no real organization or transaction")
    document._doc.info.producer = GENERATOR
    width, height = letter
    y = height - 60

    def line(text: str, size: int = 12, gap: int = 24) -> None:
        nonlocal y
        document.setFont("Helvetica-Bold" if size >= 18 else "Helvetica", size)
        document.drawString(60, y, text)
        y -= gap

    line(invoice["vendor"], 20, 30)
    line("Test fixture only - no real organization, person, account, or transaction.", 10, 34)
    line(f"Invoice: {invoice['invoice_number']}")
    line(f"Date: {invoice['date']}", gap=36)
    line("VENDOR INVOICE", 18, 34)
    line(f"Description: {invoice['description']}")
    line(f"Amount: {money(invoice['printed_subtotal'])}", gap=32)
    line(f"Printed subtotal: {money(invoice['printed_subtotal'])}")
    if Decimal(invoice["adjustment"]):
        line(f"Approved adjustment: {money(invoice['adjustment'])}")
    line(f"Approved claim total: {money(invoice['approved_total'])}", gap=36)
    line("APPROVAL NOTE", 14)
    line(invoice["note"], 10)
    document.setFont("Courier-Bold", 14)
    document.drawString(
        60, y, f"Expense reference: VENDOR-INVOICE-{invoice['expense_id']}"
    )
    document.showPage()
    document.save()


def vendor_png(path: Path, invoice: dict[str, str]) -> None:
    image = Image.new("RGB", (1020, 1320), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=24)
    title = ImageFont.load_default(size=38)
    lines = [
        (invoice["vendor"], title),
        ("Test fixture only - no real organization or transaction.", font),
        (f"Invoice: {invoice['invoice_number']}", font),
        (f"Date: {invoice['date']}", font),
        ("VENDOR INVOICE", title),
        (f"Description: {invoice['description']}", font),
        (f"Amount: {money(invoice['printed_subtotal'])}", font),
        (f"Approved claim total: {money(invoice['approved_total'])}", font),
        (invoice["note"], font),
        (f"Expense reference: VENDOR-INVOICE-{invoice['expense_id']}", font),
    ]
    y = 70
    for text, selected_font in lines:
        draw.text((70, y), text, fill="black", font=selected_font)
        y += 90 if selected_font is title else 62
    image.save(path, format="PNG", optimize=False, compress_level=9)


def text_pdf(path: Path, text: str, title: str) -> None:
    document = canvas.Canvas(
        str(path), pagesize=letter, pageCompression=1, invariant=1
    )
    document.setAuthor(GENERATOR)
    document.setCreator(GENERATOR)
    document.setTitle(title)
    document.setSubject("Closed synthetic document-intake fixture")
    document._doc.info.producer = GENERATOR
    y = letter[1] - 60
    for index, value in enumerate(text.splitlines()):
        document.setFont("Helvetica-Bold" if index == 0 else "Helvetica", 16 if index == 0 else 11)
        document.drawString(60, y, value)
        y -= 28 if index == 0 else 22
    document.showPage()
    document.save()


def document_intake_catalog(scenario: dict, files: Path) -> dict:
    source = scenario["documentIntake"]
    fixtures = {item["id"]: item for item in source["fixtures"]}
    negatives = [
        item for item in source["fixtures"]
        if item["expectedOutcome"] == "needs_profile_review"
    ]
    for fixture in source["fixtures"]:
        target = files / fixture["filename"]
        if not target.exists():
            text_pdf(target, fixture["ocrText"], "Synthetic document-intake fixture")

    profiles = []
    for source_profile in source["profiles"]:
        supported = [fixtures[fixture_id] for fixture_id in source_profile["fixtureIds"]]
        definition = {
            key: value for key, value in source_profile.items() if key != "fixtureIds"
        }
        definition.update(
            {
                "contractId": scenario["contract"]["id"],
                "fingerprintSpecification": source["fingerprintSpecification"],
                "acceptedFingerprints": sorted(
                    {
                        analyze_profile(
                            definition,
                            fixture["ocrText"],
                            fixture["mediaType"],
                        ).fingerprint
                        for fixture in supported
                    }
                ),
            }
        )
        fixture_set_id = f"fixture-set-{definition['profileKey']}-v1"
        fixture_set_body = {
            "id": fixture_set_id,
            "version": "1",
            "cases": supported + negatives,
        }
        fixture_set_body["contentHash"] = content_hash(fixture_set_body)
        evaluation_id = f"profile-evaluation-{definition['profileKey']}-v1"
        definition.update(
            {
                "lifecycle": "approved",
                "fixtureSet": {
                    "kind": "profile_fixture_set",
                    "id": fixture_set_id,
                    "version": "1",
                    "sha256": fixture_set_body["contentHash"],
                },
                "evaluationEvidence": None,
            }
        )
        definition["contentHash"] = content_hash(
            {
                key: value
                for key, value in definition.items()
                if key not in {"lifecycle", "evaluationEvidence", "contentHash"}
            }
        )
        evaluation = evaluate_profile(
            definition,
            fixture_set_body["cases"],
            ocr_version="fixture-transcript-v1",
        )
        evidence = {
            "id": evaluation_id,
            "profileVersion": {
                "kind": "document_profile",
                "id": definition["id"],
                "version": definition["version"],
                "sha256": definition["contentHash"],
            },
            "fixtureSet": definition["fixtureSet"],
            **evaluation,
        }
        definition["evaluationEvidence"] = {
            "kind": "profile_evaluation",
            "id": evaluation_id,
            "version": EVALUATION_SUITE_VERSION,
            "sha256": evidence["resultHash"],
        }
        profiles.append(
            {
                "profile": definition,
                "fixtureSet": fixture_set_body,
                "evaluationEvidence": evidence,
            }
        )
    return {
        "catalogVersion": source["catalogVersion"],
        "fingerprintSpecificationVersion": FINGERPRINT_SPECIFICATION_VERSION,
        "parserVersion": PROFILE_PARSER_VERSION,
        "evaluationSuiteVersion": EVALUATION_SUITE_VERSION,
        "profiles": profiles,
        "negativeFixtureIds": [item["id"] for item in negatives],
    }


def generate(root: Path) -> dict[str, str]:
    scenario_path = root / "scenario.json"
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    data = scenario["fixtureData"]
    files = root / "files"
    files.mkdir(parents=True, exist_ok=True)

    ledger_rows = data["ledgerRows"]
    with (files / "ledger-june-2026.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=LEDGER_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger_rows)
    workbook(files / "ledger-june-2026.xlsx", "June Ledger", LEDGER_FIELDS, ledger_rows)
    workbook(
        files / "payroll-june-2026.xlsx",
        "June Payroll",
        ("employee_reference", "service_period", "budget_category", "amount"),
        data["payrollRows"],
    )

    for invoice in data["vendorInvoices"]:
        expense = invoice["expense_id"].lower()
        vendor_pdf(files / f"vendor-invoice-{expense}.pdf", invoice)
        if invoice["expense_id"] == "EXP-004":
            vendor_png(files / f"vendor-invoice-{expense}.png", invoice)

    catalog = document_intake_catalog(scenario, files)
    (root / "document-intake-catalog.json").write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    hashes = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted(files.iterdir())
        if path.is_file()
    }
    (root / "fixture-hashes.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "packages" / "test-fixtures",
    )
    args = parser.parse_args()
    hashes = generate(args.root)
    print(f"Generated {len(hashes)} deterministic synthetic fixture files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
