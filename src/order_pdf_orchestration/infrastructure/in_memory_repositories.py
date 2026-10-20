"""In-memory implementations of the repository ports (demo app and unit tests)."""
from __future__ import annotations

from order_pdf_orchestration.application.ports.repositories import (
    OrderRequestRepository,
    SupplierOfferRepository,
    SupplierRepository,
)
from order_pdf_orchestration.domain.entities import OrderRequest, Supplier, SupplierOffer


class InMemorySupplierRepository(SupplierRepository):
    def __init__(self, suppliers: list[Supplier] | None = None) -> None:
        self._store = {s.id: s for s in (suppliers or [])}

    def get_by_id(self, supplier_id: str) -> Supplier | None:
        return self._store.get(supplier_id)

    def list_all(self) -> list[Supplier]:
        return list(self._store.values())


class InMemorySupplierOfferRepository(SupplierOfferRepository):
    def __init__(self) -> None:
        self._store: dict[str, SupplierOffer] = {}

    def save(self, offer: SupplierOffer) -> None:
        self._store[offer.id] = offer

    def get_by_id(self, offer_id: str) -> SupplierOffer | None:
        return self._store.get(offer_id)


class InMemoryOrderRequestRepository(OrderRequestRepository):
    def __init__(self) -> None:
        self._store: dict[str, OrderRequest] = {}

    def save(self, order: OrderRequest) -> None:
        self._store[order.id] = order

    def get_by_id(self, order_id: str) -> OrderRequest | None:
        return self._store.get(order_id)


def default_suppliers() -> list[Supplier]:
    """Demo suppliers for the in-memory app."""
    return [
        Supplier("SUP-OT", "Office Tech AG", "orders@officetech.example"),
        Supplier("SUP-FS", "Furniture Swiss GmbH", "sales@furniture-swiss.example"),
    ]
