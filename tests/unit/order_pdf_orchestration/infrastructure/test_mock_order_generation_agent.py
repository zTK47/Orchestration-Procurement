"""MockOrderGenerationAgent (ADR-007) and its Pydantic boundary check (ADR-008)."""
from decimal import Decimal

import pytest

from order_pdf_orchestration.application.ports.order_generation_agent import OrderGenerationError
from order_pdf_orchestration.domain.entities import OrderLineItem, SupplierOffer
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.infrastructure.mock_order_generation_agent import (
    MockOrderGenerationAgent,
)

OFFER = SupplierOffer(
    id="OF-1",
    supplier_id="SUP-1",
    raw_text=(
        "Offer 2026-118, valid 30 days\n"
        "Dell Latitude 5440 Laptop - CHF 1'250.00\n"
        "Logitech MX Keys Keyboard: 89.90 CHF\n"
        "USB-C Docking Station - CHF 189.00\n"
    ),
)


def summary(items: list[OrderLineItem]) -> list[tuple[str, int, Money]]:
    return [(i.description, i.quantity, i.unit_price) for i in items]


def test_prompt_items_are_matched_to_offer_lines_with_quantity_and_price():
    items = MockOrderGenerationAgent().generate("I need 3 Dell Latitude laptops and 5 MX Keys keyboards", OFFER)

    assert summary(items) == [
        ("Dell Latitude 5440 Laptop", 3, Money(Decimal("1250.00"), "CHF")),
        ("Logitech MX Keys Keyboard", 5, Money(Decimal("89.90"), "CHF")),
    ]
    assert [i.id for i in items] == ["LI-1", "LI-2"]


def test_missing_quantity_defaults_to_one():
    items = MockOrderGenerationAgent().generate("a docking station please", OFFER)
    assert summary(items) == [("USB-C Docking Station", 1, Money(Decimal("189.00"), "CHF"))]


def test_item_not_in_the_offer_is_kept_with_price_zero_for_validation_to_flag():
    items = MockOrderGenerationAgent().generate("2 office chairs, 1 docking station", OFFER)

    assert summary(items) == [
        ("office chairs", 2, Money(Decimal(0), "CHF")),
        ("USB-C Docking Station", 1, Money(Decimal("189.00"), "CHF")),
    ]


def test_partial_keyword_overlap_is_not_treated_as_a_match():
    items = MockOrderGenerationAgent().generate("4 USB-C monitors", OFFER)
    assert summary(items) == [("USB-C monitors", 4, Money(Decimal(0), "CHF"))]


def test_valid_raw_output_is_converted_to_domain_line_items():
    items = MockOrderGenerationAgent().to_line_items(
        {"line_items": [{"description": "Dock", "quantity": "2", "unit_price": "189.00", "currency": "CHF"}]}
    )
    assert summary(items) == [("Dock", 2, Money(Decimal("189.00"), "CHF"))]


@pytest.mark.parametrize(
    "raw",
    [
        {"line_items": [{"description": "Dock", "quantity": 0, "unit_price": "1", "currency": "CHF"}]},
        {"line_items": [{"description": "Dock", "quantity": 1, "unit_price": "-1", "currency": "CHF"}]},
        {"line_items": [{"description": "", "quantity": 1, "unit_price": "1", "currency": "CHF"}]},
        {"line_items": [{"description": "Dock", "quantity": 1, "unit_price": "cheap", "currency": "CHF"}]},
        {"line_items": [{"description": "Dock", "quantity": 1, "unit_price": "1", "currency": "francs"}]},
        {"items": []},
    ],
    ids=["zero-quantity", "negative-price", "blank-description", "non-numeric-price", "bad-currency", "wrong-shape"],
)
def test_malformed_raw_output_is_rejected_at_the_boundary(raw):
    with pytest.raises(OrderGenerationError):
        MockOrderGenerationAgent().to_line_items(raw)
