from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from procurement.application.ports.repositories import CatalogItemRepository
from procurement.domain.entities import CatalogItem
from procurement.domain.value_objects import SKU, Money
from procurement.infrastructure.models import CatalogItemModel


def _to_domain(model: CatalogItemModel) -> CatalogItem:
    return CatalogItem(
        id=model.id,
        sku=SKU(model.sku),
        product_name=model.product_name,
        category=model.category,
        supplier_id=model.supplier_id,
        unit_price=Money(Decimal(str(model.unit_price)), model.currency),
        stock_qty=model.stock_qty,
        lead_time_days=model.lead_time_days,
    )


class SqlAlchemyCatalogItemRepository(CatalogItemRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[CatalogItem]:
        models = self._session.scalars(select(CatalogItemModel)).all()
        return [_to_domain(m) for m in models]
