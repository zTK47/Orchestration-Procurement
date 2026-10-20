from decimal import Decimal

from procurement.domain.value_objects import Money
from procurement.infrastructure.models import CatalogItemModel, SupplierModel
from procurement.infrastructure.repositories.sqlalchemy_catalog_item_repository import (
    SqlAlchemyCatalogItemRepository,
)
from procurement.infrastructure.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)


def test_catalog_item_repository_lists_all_items(db_session):
    db_session.add(SupplierModel(id="SUP-INT-1", name="Test Supplier", approved=True))
    db_session.add(
        CatalogItemModel(
            id="CAT-INT-1", sku="SKU-INT-1", product_name="Test Laptop", category="Laptop",
            supplier_id="SUP-INT-1", unit_price=Decimal("999.00"), currency="CHF",
            stock_qty=10, lead_time_days=5,
        )
    )
    db_session.commit()

    repository = SqlAlchemyCatalogItemRepository(db_session)
    items = repository.list_all()

    matching = [i for i in items if i.sku.value == "SKU-INT-1"]
    assert len(matching) == 1
    assert matching[0].unit_price == Money(Decimal("999.00"), "CHF")


def test_supplier_repository_returns_all_suppliers_keyed_by_id(db_session):
    db_session.add(SupplierModel(id="SUP-INT-2", name="Approved Supplier", approved=True))
    db_session.add(SupplierModel(id="SUP-INT-3", name="Unapproved Supplier", approved=False))
    db_session.commit()

    repository = SqlAlchemySupplierRepository(db_session)
    suppliers = repository.get_all_by_id()

    assert suppliers["SUP-INT-2"].approved is True
    assert suppliers["SUP-INT-3"].approved is False
