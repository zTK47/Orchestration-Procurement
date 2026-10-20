from decimal import Decimal

import pytest

from procurement.application.use_cases.submit_catalog_selection import (
    SubmitCatalogSelectionUseCase,
)
from procurement.domain.entities import CatalogItem, ProcurementRequest, ProcurementStatus, Supplier
from procurement.domain.exceptions import SelectedItemUnavailableError
from procurement.domain.value_objects import SKU, Money
from procurement.infrastructure.in_memory_repositories import (
    InMemoryCatalogItemRepository,
    InMemoryProcurementRequestRepository,
    InMemorySupplierRepository,
)


def make_use_case(catalog_items, suppliers):
    return SubmitCatalogSelectionUseCase(
        catalog_repository=InMemoryCatalogItemRepository(catalog_items),
        supplier_repository=InMemorySupplierRepository(suppliers),
        procurement_repository=InMemoryProcurementRequestRepository(),
    )


def make_item(sku="SKU-1", approved_supplier=True, stock=10, price="1200.00"):
    supplier_id = "SUP-1" if approved_supplier else "SUP-2"
    item = CatalogItem(
        id="CAT-1",
        sku=SKU(sku),
        product_name="Lenovo Laptop",
        category="Laptop",
        supplier_id=supplier_id,
        unit_price=Money(Decimal(price), "CHF"),
        stock_qty=stock,
        lead_time_days=5,
    )
    suppliers = [
        Supplier(id="SUP-1", name="Approved Co", approved=True),
        Supplier(id="SUP-2", name="Unapproved Co", approved=False),
    ]
    return item, suppliers


def new_request() -> ProcurementRequest:
    return ProcurementRequest(id="PR-1", requester_id="U-1", cost_center_id="CC-1")


def test_direct_selection_resolves_immediately_with_correct_total():
    item, suppliers = make_item(price="1200.00")
    use_case = make_use_case([item], suppliers)

    result = use_case.execute(new_request(), SKU("SKU-1"), quantity=3)

    assert result.status == ProcurementStatus.RESOLVED
    assert result.amount == Money(Decimal("3600.00"), "CHF")  # 1200 * 3
    assert result.stock_check == "PASSED"


def test_direct_selection_rejects_unknown_sku():
    item, suppliers = make_item()
    use_case = make_use_case([item], suppliers)

    with pytest.raises(SelectedItemUnavailableError):
        use_case.execute(new_request(), SKU("UNKNOWN-SKU"), quantity=1)


def test_direct_selection_rejects_unapproved_supplier():
    item, suppliers = make_item(approved_supplier=False)
    use_case = make_use_case([item], suppliers)

    with pytest.raises(SelectedItemUnavailableError):
        use_case.execute(new_request(), SKU("SKU-1"), quantity=1)


def test_direct_selection_rejects_insufficient_stock():
    item, suppliers = make_item(stock=2)
    use_case = make_use_case([item], suppliers)

    with pytest.raises(SelectedItemUnavailableError):
        use_case.execute(new_request(), SKU("SKU-1"), quantity=5)
