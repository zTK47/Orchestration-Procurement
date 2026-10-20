"""Repository ports (abstract interfaces).

The Application layer depends on these abstractions, never on concrete
implementations. Concrete implementations (in-memory for now, SQLAlchemy
later) live in the Infrastructure layer and are injected at wiring time
(see infrastructure/main.py). This is Dependency Inversion in practice --
see docs/adr/ADR-003-dependency-injection-via-ports.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from procurement.domain.entities import (
    Approval,
    CatalogItem,
    CostCenter,
    ProcurementRequest,
    Supplier,
    User,
)


class ProcurementRequestRepository(ABC):
    @abstractmethod
    def save(self, request: ProcurementRequest) -> None: ...

    @abstractmethod
    def get_by_id(self, request_id: str) -> ProcurementRequest | None: ...


class CatalogItemRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[CatalogItem]: ...


class SupplierRepository(ABC):
    @abstractmethod
    def get_all_by_id(self) -> dict[str, Supplier]:
        """Returns all suppliers keyed by their id, for fast lookup during
        sourcing."""
        ...


class CostCenterRepository(ABC):
    @abstractmethod
    def get_by_id(self, cost_center_id: str) -> CostCenter | None: ...

    @abstractmethod
    def save(self, cost_center: CostCenter) -> None: ...


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...


class ApprovalRepository(ABC):
    @abstractmethod
    def save(self, approval: Approval) -> None: ...

    @abstractmethod
    def list_for_request(self, procurement_request_id: str) -> list[Approval]: ...
