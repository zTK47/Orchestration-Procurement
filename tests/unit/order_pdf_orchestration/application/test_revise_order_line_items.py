"""OPO-UC-006 - see docs/specs/OPO-UC-006-revise-order-line-items.md"""
from decimal import Decimal

import pytest

from order_pdf_orchestration.application.use_cases.revise_order_line_items import (
    ReviseOrderLineItemsUseCase,
)
from order_pdf_orchestration.application.use_cases.validate_order_request import (
    ValidateOrderRequestUseCase,
)
from order_pdf_orchestration.domain.entities import (
    OrderLineItem,
    OrderRequest,
    OrderStatus,
    SupplierOffer,
)
from order_pdf_orchestration.domain.exceptions import (
    EmptyOrderRequestError,
    IllegalStatusTransitionError,
)
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.infrastructure.in_memory_repositories import (
    InMemoryOrderRequestRepository,
    InMemorySupplierOfferRepository,
)


def line(description: str) -> OrderLineItem:
    return OrderLineItem(id="LI-1", description=description, quantity=1, unit_price=Money(Decimal(189), "CHF"))


def needs_clarification() -> OrderRequest:
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="1 docking thing")
    order.mark_generated([line("Docking thing")])
    order.mark_needs_clarification(["Line item 'Docking thing' does not match anything in the supplier offer."])
    return order


def test_human_revision_returns_the_request_to_generated_and_saves_it():
    orders = InMemoryOrderRequestRepository()

    result = ReviseOrderLineItemsUseCase(order_repository=orders).execute(
        needs_clarification(), [line("USB-C Docking Station")]
    )

    assert result.status == OrderStatus.GENERATED
    assert result.validation_notes == []
    assert orders.get_by_id("OR-1") is result


def test_after_the_revision_validation_decides_again():
    offers = InMemorySupplierOfferRepository()
    offers.save(SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text="USB-C Docking Station - CHF 189.00"))
    orders = InMemoryOrderRequestRepository()
    order = ReviseOrderLineItemsUseCase(order_repository=orders).execute(
        needs_clarification(), [line("USB-C Docking Station")]
    )

    result = ValidateOrderRequestUseCase(offer_repository=offers, order_repository=orders).execute(order)

    assert result.status == OrderStatus.VALIDATED


def test_revision_with_no_line_items_is_refused():
    with pytest.raises(EmptyOrderRequestError):
        ReviseOrderLineItemsUseCase(order_repository=InMemoryOrderRequestRepository()).execute(
            needs_clarification(), []
        )


def test_only_a_request_needing_clarification_can_be_revised():
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="...")
    order.mark_generated([line("USB-C Docking Station")])

    with pytest.raises(IllegalStatusTransitionError):
        ReviseOrderLineItemsUseCase(order_repository=InMemoryOrderRequestRepository()).execute(
            order, [line("USB-C Docking Station")]
        )
