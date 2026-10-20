"""Repository ports. Implementations live in infrastructure/ (in-memory in this slice)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from order_pdf_orchestration.domain.entities import OrderRequest, Supplier, SupplierOffer


class SupplierRepository(ABC):
    @abstractmethod
    def get_by_id(self, supplier_id: str) -> Supplier | None: ...

    @abstractmethod
    def list_all(self) -> list[Supplier]: ...


class SupplierOfferRepository(ABC):
    @abstractmethod
    def save(self, offer: SupplierOffer) -> None: ...

    @abstractmethod
    def get_by_id(self, offer_id: str) -> SupplierOffer | None: ...


class OrderRequestRepository(ABC):
    @abstractmethod
    def save(self, order: OrderRequest) -> None: ...

    @abstractmethod
    def get_by_id(self, order_id: str) -> OrderRequest | None: ...
