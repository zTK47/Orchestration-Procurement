"""In-memory repository implementations.

These satisfy the Application layer's abstract ports and are used for the
initial prototype, the demo script (see main.py) and as fakes in unit tests.
They will be replaced by SQLAlchemy-backed repositories (see db.py /
models.py) during Phase 4 (Validate) without any change to the Application
or Domain layers -- this is the whole point of Dependency Inversion.
"""
from __future__ import annotations

from procurement.application.ports.repositories import (
    ApprovalRepository,
    CatalogItemRepository,
    CostCenterRepository,
    ProcurementRequestRepository,
    SupplierRepository,
    UserRepository,
)
from procurement.domain.entities import (
    Approval,
    CatalogItem,
    CostCenter,
    ProcurementRequest,
    Supplier,
    User,
)


class InMemoryProcurementRequestRepository(ProcurementRequestRepository):
    def __init__(self) -> None:
        self._store: dict[str, ProcurementRequest] = {}

    def save(self, request: ProcurementRequest) -> None:
        self._store[request.id] = request

    def get_by_id(self, request_id: str) -> ProcurementRequest | None:
        return self._store.get(request_id)


class InMemoryCatalogItemRepository(CatalogItemRepository):
    def __init__(self, items: list[CatalogItem] | None = None) -> None:
        self._items = items or []

    def list_all(self) -> list[CatalogItem]:
        return list(self._items)


class InMemorySupplierRepository(SupplierRepository):
    def __init__(self, suppliers: list[Supplier] | None = None) -> None:
        self._suppliers = {s.id: s for s in (suppliers or [])}

    def get_all_by_id(self) -> dict[str, Supplier]:
        return dict(self._suppliers)


class InMemoryCostCenterRepository(CostCenterRepository):
    def __init__(self, cost_centers: list[CostCenter] | None = None) -> None:
        self._store: dict[str, CostCenter] = {c.id: c for c in (cost_centers or [])}

    def get_by_id(self, cost_center_id: str) -> CostCenter | None:
        return self._store.get(cost_center_id)

    def save(self, cost_center: CostCenter) -> None:
        self._store[cost_center.id] = cost_center


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self._store: dict[str, User] = {u.id: u for u in (users or [])}

    def get_by_id(self, user_id: str) -> User | None:
        return self._store.get(user_id)


class InMemoryApprovalRepository(ApprovalRepository):
    def __init__(self) -> None:
        self._store: list[Approval] = []

    def save(self, approval: Approval) -> None:
        self._store.append(approval)

    def list_for_request(self, procurement_request_id: str) -> list[Approval]:
        return [a for a in self._store if a.procurement_request_id == procurement_request_id]
