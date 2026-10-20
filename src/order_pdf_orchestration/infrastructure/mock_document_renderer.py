"""Renders an OrderRequest as a real one-page PDF with fpdf2 (see docs/PROJECT.md).

"Mock" only in the sense that it writes to a local directory instead of a document
service. Page streams are left uncompressed so the text stays inspectable in tests.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fpdf import FPDF

from order_pdf_orchestration.application.ports.document_renderer import DocumentRenderer
from order_pdf_orchestration.domain.entities import OrderRequest, Supplier


def _latin1(text: str) -> str:
    """The built-in PDF fonts only cover Latin-1; replace anything else."""
    return text.translate({0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0x2013: "-"}).encode(
        "latin-1", "replace"
    ).decode("latin-1")


class MockDocumentRenderer(DocumentRenderer):
    def __init__(self, output_dir: Path | str | None = None) -> None:
        self._dir = Path(output_dir or Path(tempfile.gettempdir()) / "order_pdfs")
        self._dir.mkdir(parents=True, exist_ok=True)

    def render(self, order: OrderRequest, supplier: Supplier) -> str:
        pdf = FPDF()
        pdf.set_compression(False)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Purchase Order", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        for label, value in (
            ("Order request", order.id),
            ("Supplier", f"{supplier.name} ({supplier.contact_reference})"),
            ("Supplier offer", order.supplier_offer_id),
        ):
            pdf.cell(0, 6, _latin1(f"{label}: {value}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        widths = (90, 20, 35, 35)
        pdf.set_font("Helvetica", "B", 10)
        for width, header in zip(widths, ("Description", "Qty", "Unit price", "Line total")):
            pdf.cell(width, 7, header, border=1)
        pdf.ln()
        pdf.set_font("Helvetica", size=10)
        for item in order.line_items:
            currency = item.unit_price.currency
            row = (
                item.description,
                str(item.quantity),
                f"{currency} {item.unit_price.amount:.2f}",
                f"{currency} {item.line_total().amount:.2f}",
            )
            for width, value in zip(widths, row):
                pdf.cell(width, 7, _latin1(value), border=1)
            pdf.ln()

        total = order.total()
        if total is not None:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(sum(widths[:3]), 7, "Total", border=1)
            pdf.cell(widths[3], 7, f"{total.currency} {total.amount:.2f}", border=1)

        reference = f"order-{order.id}.pdf"
        pdf.output(str(self._dir / reference))
        return reference

    def read(self, pdf_reference: str) -> bytes:
        if Path(pdf_reference).name != pdf_reference:
            raise FileNotFoundError(pdf_reference)
        return (self._dir / pdf_reference).read_bytes()
