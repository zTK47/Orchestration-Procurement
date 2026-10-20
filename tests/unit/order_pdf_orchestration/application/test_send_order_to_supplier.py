"""OPO-UC-005 - see docs/specs/OPO-UC-005-send-order-to-supplier.md"""
from decimal import Decimal

import pytest

from order_pdf_orchestration.application.ports.supplier_gateway import (
    SupplierGateway,
    SupplierGatewayError,
)
from order_pdf_orchestration.application.use_cases.send_order_to_supplier import (
    SendOrderToSupplierUseCase,
)
from order_pdf_orchestration.domain.entities import (
    OrderLineItem,
    OrderRequest,
    OrderStatus,
    Supplier,
    SupplierOffer,
)
from order_pdf_orchestration.domain.exceptions import (
    IllegalStatusTransitionError,
    PdfNotRenderedError,
)
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.infrastructure.in_memory_repositories import (
    InMemoryOrderRequestRepository,
    InMemorySupplierOfferRepository,
    InMemorySupplierRepository,
)
from order_pdf_orchestration.infrastructure.mock_supplier_gateway import MockSupplierGateway


class FailingGateway(SupplierGateway):
    def send_order(self, order, supplier):
        raise SupplierGatewayError("supplier portal unreachable")


def use_case(gateway: SupplierGateway, orders=None) -> SendOrderToSupplierUseCase:
    suppliers = InMemorySupplierRepository([Supplier("SUP-1", "Office Tech AG", "orders@officetech.example")])
    offers = InMemorySupplierOfferRepository()
    offers.save(SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text="MX Keys Keyboard CHF 89.90"))
    return SendOrderToSupplierUseCase(
        gateway=gateway,
        supplier_repository=suppliers,
        offer_repository=offers,
        order_repository=orders or InMemoryOrderRequestRepository(),
    )


def validated(with_pdf: bool = True) -> OrderRequest:
    order = OrderRequest(id="7c1e9a20-0000", supplier_offer_id="OF-1", prompt_text="5 MX Keys")
    order.mark_generated(
        [OrderLineItem(id="LI-1", description="MX Keys Keyboard", quantity=5, unit_price=Money(Decimal("89.90"), "CHF"))]
    )
    order.mark_validated()
    if with_pdf:
        order.attach_pdf("7c1e9a20-0000.pdf")
    return order


def test_validated_order_with_pdf_is_sent_and_saved():
    gateway = MockSupplierGateway()
    orders = InMemoryOrderRequestRepository()

    result = use_case(gateway, orders).execute(validated())

    assert result.status == OrderStatus.SENT
    assert result.supplier_reference == "SUP-ORD-7C1E9A20"
    assert gateway.sent == [("7c1e9a20-0000", "SUP-1", "7c1e9a20-0000.pdf")]
    assert orders.get_by_id("7c1e9a20-0000") is result


def test_rule_5_order_that_is_not_validated_is_not_sent():
    gateway = MockSupplierGateway()
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="...")

    with pytest.raises(IllegalStatusTransitionError):
        use_case(gateway).execute(order)

    assert gateway.sent == []


def test_order_without_pdf_is_not_sent():
    gateway = MockSupplierGateway()

    with pytest.raises(PdfNotRenderedError):
        use_case(gateway).execute(validated(with_pdf=False))

    assert gateway.sent == []


def test_rule_6_a_sent_order_is_never_sent_twice():
    gateway = MockSupplierGateway()
    send = use_case(gateway)
    order = send.execute(validated())

    with pytest.raises(IllegalStatusTransitionError):
        send.execute(order)

    assert len(gateway.sent) == 1


def test_gateway_failure_leaves_the_order_validated():
    order = validated()

    with pytest.raises(SupplierGatewayError):
        use_case(FailingGateway()).execute(order)

    assert order.status == OrderStatus.VALIDATED
    assert order.supplier_reference is None
