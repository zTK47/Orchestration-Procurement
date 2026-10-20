"""OPO-UC-003 - see docs/specs/OPO-UC-003-validate-order-request.md"""
from decimal import Decimal

import pytest

from order_pdf_orchestration.application.use_cases.validate_order_request import (
    ValidateOrderRequestUseCase,
)
from order_pdf_orchestration.domain.entities import (
    OrderLineItem,
    OrderRequest,
    OrderStatus,
    SupplierOffer,
)
from order_pdf_orchestration.domain.exceptions import IllegalStatusTransitionError
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.infrastructure.in_memory_repositories import (
    InMemoryOrderRequestRepository,
    InMemorySupplierOfferRepository,
)


def line(description: str) -> OrderLineItem:
    return OrderLineItem(id="LI-1", description=description, quantity=2, unit_price=Money(Decimal(10), "CHF"))


def setup():
    offers = InMemorySupplierOfferRepository()
    offers.save(SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text="Logitech MX Keys Keyboard - CHF 89.90"))
    orders = InMemoryOrderRequestRepository()
    return ValidateOrderRequestUseCase(offer_repository=offers, order_repository=orders), orders


def generated(*descriptions: str) -> OrderRequest:
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="...")
    order.mark_generated([line(d) for d in descriptions])
    return order


def test_matching_order_becomes_validated_and_is_saved():
    use_case, orders = setup()

    result = use_case.execute(generated("MX Keys Keyboard"))

    assert result.status == OrderStatus.VALIDATED
    assert result.validation_notes == []
    assert orders.get_by_id("OR-1") is result


def test_unmatched_item_goes_to_a_human_and_is_not_auto_approved():
    use_case, orders = setup()

    result = use_case.execute(generated("MX Keys Keyboard", "Standing Desk"))

    assert result.status == OrderStatus.NEEDS_CLARIFICATION
    assert len(result.validation_notes) == 1
    assert "Standing Desk" in result.validation_notes[0]
    assert orders.get_by_id("OR-1") is result


def test_order_without_line_items_needs_clarification():
    use_case, _ = setup()

    result = use_case.execute(generated())

    assert result.status == OrderStatus.NEEDS_CLARIFICATION
    assert result.validation_notes == ["The order request has no line items."]


def test_an_already_validated_request_is_not_revalidated():
    use_case, _ = setup()
    order = generated("MX Keys Keyboard")
    use_case.execute(order)

    with pytest.raises(IllegalStatusTransitionError):
        use_case.execute(order)
