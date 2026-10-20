"""MockDocumentRenderer writes a real PDF file (fpdf2), not a stub string."""
from decimal import Decimal

import pytest

from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest, Supplier
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.infrastructure.mock_document_renderer import MockDocumentRenderer

SUPPLIER = Supplier("SUP-1", "Office Tech AG", "orders@officetech.example")


def validated_order() -> OrderRequest:
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="3 laptops and 5 keyboards")
    order.mark_generated(
        [
            OrderLineItem(id="LI-1", description="Dell Latitude 5440 Laptop", quantity=3,
                          unit_price=Money(Decimal("1250.00"), "CHF")),
            OrderLineItem(id="LI-2", description="Bürostuhl “Ergo” – Modell 7", quantity=5,
                          unit_price=Money(Decimal("89.90"), "CHF")),
        ]
    )
    order.mark_validated()
    return order


def test_render_writes_a_real_pdf_and_returns_a_reference(tmp_path):
    renderer = MockDocumentRenderer(output_dir=tmp_path)

    reference = renderer.render(validated_order(), SUPPLIER)

    assert reference == "order-OR-1.pdf"
    content = (tmp_path / reference).read_bytes()
    assert content.startswith(b"%PDF-")
    assert content.rstrip().endswith(b"%%EOF")


def test_pdf_contains_supplier_line_items_and_total(tmp_path):
    renderer = MockDocumentRenderer(output_dir=tmp_path)

    content = renderer.read(renderer.render(validated_order(), SUPPLIER))

    for expected in (b"Office Tech AG", b"Dell Latitude 5440 Laptop", b"CHF 4199.50"):
        assert expected in content


def test_read_refuses_a_reference_that_is_not_a_plain_file_name(tmp_path):
    with pytest.raises(FileNotFoundError):
        MockDocumentRenderer(output_dir=tmp_path).read("../secrets.pdf")
