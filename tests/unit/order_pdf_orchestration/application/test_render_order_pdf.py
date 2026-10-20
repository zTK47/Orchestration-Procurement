"""OPO-UC-004 - see docs/specs/OPO-UC-004-render-order-pdf.md"""
from decimal import Decimal

import pytest

from order_pdf_orchestration.application.ports.document_renderer import DocumentRenderer
from order_pdf_orchestration.application.use_cases.render_order_pdf import RenderOrderPdfUseCase
from order_pdf_orchestration.domain.entities import (
    OrderLineItem,
    OrderRequest,
    OrderStatus,
    Supplier,
    SupplierOffer,
)
from order_pdf_orchestration.domain.exceptions import OrderNotValidatedError
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.infrastructure.in_memory_repositories import (
    InMemoryOrderRequestRepository,
    InMemorySupplierOfferRepository,
    InMemorySupplierRepository,
)


class FakeRenderer(DocumentRenderer):
    def __init__(self) -> None:
        self.rendered: list[tuple[str, str]] = []

    def render(self, order, supplier):
        self.rendered.append((order.id, supplier.id))
        return f"{order.id}.pdf"

    def read(self, pdf_reference):
        return b"%PDF-fake"


def setup(renderer: FakeRenderer):
    suppliers = InMemorySupplierRepository([Supplier("SUP-1", "Office Tech AG", "orders@officetech.example")])
    offers = InMemorySupplierOfferRepository()
    offers.save(SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text="MX Keys Keyboard CHF 89.90"))
    orders = InMemoryOrderRequestRepository()
    use_case = RenderOrderPdfUseCase(
        renderer=renderer, supplier_repository=suppliers, offer_repository=offers, order_repository=orders
    )
    return use_case, orders


def generated() -> OrderRequest:
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="5 MX Keys")
    order.mark_generated(
        [OrderLineItem(id="LI-1", description="MX Keys Keyboard", quantity=5, unit_price=Money(Decimal("89.90"), "CHF"))]
    )
    return order


def test_validated_request_gets_a_pdf_reference_and_is_saved():
    renderer = FakeRenderer()
    use_case, orders = setup(renderer)
    order = generated()
    order.mark_validated()

    result = use_case.execute(order)

    assert renderer.rendered == [("OR-1", "SUP-1")]
    assert result.pdf_reference == "OR-1.pdf"
    assert result.status == OrderStatus.VALIDATED
    assert orders.get_by_id("OR-1") is result


def test_request_that_is_not_validated_is_not_rendered():
    renderer = FakeRenderer()
    use_case, _ = setup(renderer)
    order = generated()
    order.mark_needs_clarification(["check"])

    with pytest.raises(OrderNotValidatedError):
        use_case.execute(order)

    assert renderer.rendered == []
    assert order.pdf_reference is None
