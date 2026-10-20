"""Rule 1 and rule 2 as evaluated by the OrderValidationRule domain service."""
from decimal import Decimal

from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest, SupplierOffer
from order_pdf_orchestration.domain.services.order_validation_rule import OrderValidationRule
from order_pdf_orchestration.domain.value_objects import Money

OFFER = SupplierOffer(
    id="OF-1",
    supplier_id="SUP-1",
    raw_text=(
        "Offer 2026-118\n"
        "Dell Latitude 5440 Laptop, 14 inch - CHF 1250.00\n"
        "Logitech MX Keys Keyboard - CHF 89.90\n"
        "USB-C Docking Station - CHF 189.00\n"
    ),
)


def order_with(*descriptions: str) -> OrderRequest:
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="...")
    order.mark_generated(
        [
            OrderLineItem(id=f"LI-{n}", description=d, quantity=1, unit_price=Money(Decimal(1), "CHF"))
            for n, d in enumerate(descriptions, start=1)
        ]
    )
    return order


def test_all_line_items_found_in_the_offer_is_valid():
    result = OrderValidationRule().evaluate(
        order_with("Dell Latitude 5440 Laptop", "Logitech MX Keys Keyboard"), OFFER
    )
    assert result.is_valid
    assert result.notes == []


def test_matching_is_case_insensitive_and_tolerates_plurals():
    result = OrderValidationRule().evaluate(order_with("dell latitude LAPTOPS"), OFFER)
    assert result.is_valid


def test_rule_2_item_not_in_offer_is_not_valid_and_named_in_a_note():
    result = OrderValidationRule().evaluate(
        order_with("Dell Latitude 5440 Laptop", "Ergonomic Office Chair"), OFFER
    )
    assert not result.is_valid
    assert len(result.notes) == 1
    assert "Ergonomic Office Chair" in result.notes[0]


def test_rule_2_partial_keyword_match_is_not_enough():
    result = OrderValidationRule().evaluate(order_with("USB-C Monitor"), OFFER)
    assert not result.is_valid


def test_rule_1_no_line_items_is_not_valid():
    result = OrderValidationRule().evaluate(order_with(), OFFER)
    assert not result.is_valid
    assert result.notes == ["The order request has no line items."]
