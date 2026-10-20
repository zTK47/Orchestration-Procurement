from decimal import Decimal

from procurement.application.use_cases.resolve_item import ResolveItemUseCase
from procurement.domain.entities import (
    CatalogItem,
    ProcurementRequest,
    ProcurementStatus,
    Supplier,
)
from procurement.domain.value_objects import SKU, Money, ParsedRequest
from procurement.infrastructure.in_memory_repositories import (
    InMemoryCatalogItemRepository,
    InMemoryProcurementRequestRepository,
    InMemorySupplierRepository,
)


def test_resolve_item_sets_amount_as_unit_price_times_quantity():
    supplier = Supplier(id="SUP-001", name="Approved Co", approved=True)
    catalog_item = CatalogItem(
        id="CAT-1",
        sku=SKU("LEN-T14-G3"),
        product_name="Lenovo Laptop",
        category="Laptop",
        supplier_id="SUP-001",
        unit_price=Money(Decimal("1200.00"), "CHF"),
        stock_qty=20,
        lead_time_days=5,
    )
    procurement_repository = InMemoryProcurementRequestRepository()
    use_case = ResolveItemUseCase(
        catalog_repository=InMemoryCatalogItemRepository([catalog_item]),
        supplier_repository=InMemorySupplierRepository([supplier]),
        procurement_repository=procurement_repository,
    )
    request = ProcurementRequest(id="PR-1", requester_id="U-1", cost_center_id="CC-1")
    request.mark_parsed(ParsedRequest(quantity=5, product_name="Lenovo Laptop", category="Laptop", confidence=0.95))

    result = use_case.execute(request)

    assert result.status == ProcurementStatus.RESOLVED
    assert result.resolved_sku == SKU("LEN-T14-G3")
    assert result.amount == Money(Decimal("6000.00"), "CHF")  # 1200 * 5
