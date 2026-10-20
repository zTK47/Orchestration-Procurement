"""Rule 3: quantity > 0, unit_price >= 0. Rule 4: total = sum(quantity * unit_price)."""
from decimal import Decimal

import pytest

from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest
from order_pdf_orchestration.domain.exceptions import InvalidLineItemError
from order_pdf_orchestration.domain.value_objects import Money


def chf(amount: str) -> Money:
    return Money(Decimal(amount), "CHF")


@pytest.mark.parametrize("quantity", [0, -1])
def test_line_item_quantity_must_be_positive(quantity):
    with pytest.raises(InvalidLineItemError):
        OrderLineItem(id="LI-1", description="Dell Latitude 5440", quantity=quantity, unit_price=chf("1"))


def test_line_item_description_must_not_be_blank():
    with pytest.raises(InvalidLineItemError):
        OrderLineItem(id="LI-1", description="  ", quantity=1, unit_price=chf("1"))


def test_line_item_unit_price_cannot_be_negative():
    with pytest.raises(ValueError):
        OrderLineItem(id="LI-1", description="Dock", quantity=1, unit_price=chf("-5"))


def test_line_item_price_zero_is_allowed():
    item = OrderLineItem(id="LI-1", description="Free sample", quantity=2, unit_price=chf("0"))
    assert item.line_total() == chf("0")


def test_order_total_is_the_sum_of_quantity_times_unit_price():
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="...")
    order.line_items = [
        OrderLineItem(id="LI-1", description="Laptop", quantity=3, unit_price=chf("1250.00")),
        OrderLineItem(id="LI-2", description="Keyboard", quantity=5, unit_price=chf("89.90")),
    ]

    assert order.total() == chf("4199.50")


def test_order_total_is_none_without_line_items():
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="...")
    assert order.total() is None
