from decimal import Decimal

import pytest

from procurement.domain.entities import CatalogItem, Supplier
from procurement.domain.exceptions import (
    NoMatchingCatalogItemError,
    RequiresClarificationError,
)
from procurement.domain.services.sourcing_rules import SourcingRule
from procurement.domain.value_objects import SKU, Money, ParsedRequest


def item(id_, sku, category, supplier_id, price, stock=10, lead_time=5):
    return CatalogItem(
        id=id_,
        sku=SKU(sku),
        product_name=sku,
        category=category,
        supplier_id=supplier_id,
        unit_price=Money(Decimal(price), "CHF"),
        stock_qty=stock,
        lead_time_days=lead_time,
    )


@pytest.fixture
def suppliers():
    return {
        "SUP-001": Supplier(id="SUP-001", name="Approved Co", approved=True),
        "SUP-002": Supplier(id="SUP-002", name="Unapproved Co", approved=False),
    }


@pytest.fixture
def parsed_request():
    return ParsedRequest(quantity=5, product_name="Laptop", category="Laptop", confidence=0.9)


def test_resolves_cheapest_approved_item(suppliers, parsed_request):
    items = [
        item("A", "SKU-A", "Laptop", "SUP-001", "1200.00"),
        item("B", "SKU-B", "Laptop", "SUP-001", "999.00"),
    ]
    result = SourcingRule().resolve(parsed_request, items, suppliers)
    assert result.sku.value == "SKU-B"


def test_filters_out_unapproved_supplier(suppliers, parsed_request):
    items = [
        item("A", "SKU-A", "Laptop", "SUP-002", "500.00"),  # cheapest but unapproved
        item("B", "SKU-B", "Laptop", "SUP-001", "999.00"),
    ]
    result = SourcingRule().resolve(parsed_request, items, suppliers)
    assert result.sku.value == "SKU-B"


def test_filters_out_insufficient_stock(suppliers, parsed_request):
    items = [
        item("A", "SKU-A", "Laptop", "SUP-001", "500.00", stock=1),  # not enough stock (need 5)
        item("B", "SKU-B", "Laptop", "SUP-001", "999.00", stock=10),
    ]
    result = SourcingRule().resolve(parsed_request, items, suppliers)
    assert result.sku.value == "SKU-B"


def test_filters_out_lead_time_too_long(suppliers, parsed_request):
    items = [
        item("A", "SKU-A", "Laptop", "SUP-001", "500.00", lead_time=30),
        item("B", "SKU-B", "Laptop", "SUP-001", "999.00", lead_time=5),
    ]
    result = SourcingRule().resolve(parsed_request, items, suppliers)
    assert result.sku.value == "SKU-B"


def test_filters_by_category(suppliers, parsed_request):
    items = [
        item("A", "SKU-A", "Monitor", "SUP-001", "100.00"),
        item("B", "SKU-B", "Laptop", "SUP-001", "999.00"),
    ]
    result = SourcingRule().resolve(parsed_request, items, suppliers)
    assert result.sku.value == "SKU-B"


def test_no_matching_item_raises(suppliers, parsed_request):
    items = [item("A", "SKU-A", "Monitor", "SUP-001", "100.00")]
    with pytest.raises(NoMatchingCatalogItemError):
        SourcingRule().resolve(parsed_request, items, suppliers)


def test_price_tie_requires_clarification(suppliers, parsed_request):
    items = [
        item("A", "SKU-A", "Laptop", "SUP-001", "999.00"),
        item("B", "SKU-B", "Laptop", "SUP-001", "999.00"),
    ]
    with pytest.raises(RequiresClarificationError):
        SourcingRule().resolve(parsed_request, items, suppliers)
