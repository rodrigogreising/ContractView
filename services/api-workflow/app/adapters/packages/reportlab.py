"""Deterministic ReportLab invoice PDF adapter."""

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ReportLabInvoicePdfRenderer:
    def render(self, invoice: dict[str, Any]) -> bytes:
        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=LETTER,
            title=f"Invoice v{invoice['version']}",
            author="ContractView POC",
            invariant=1,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Reimbursement Invoice", styles["Title"]),
            Paragraph(
                f"Invoice version {invoice['version']} | "
                f"Configuration {invoice['configurationVersionId']}",
                styles["Normal"],
            ),
            Spacer(1, 12),
        ]
        rows = [["Expense", "Date", "Vendor", "Category", "Amount"]] + [
            [
                line["expenseKey"],
                line["date"],
                line["vendor"],
                line["category"],
                f"${line['amount']}",
            ]
            for line in invoice["lines"]
        ]
        table = Table(rows, repeatRows=1, colWidths=[60, 65, 150, 100, 65])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#294d37")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )
        story.extend(
            [
                table,
                Spacer(1, 14),
                Paragraph(f"Total requested: ${invoice['total']}", styles["Heading2"]),
                Paragraph("Synthetic demonstration data only", styles["Italic"]),
            ]
        )
        document.build(story)
        return output.getvalue()
