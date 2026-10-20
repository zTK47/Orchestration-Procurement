"""FastAPI dependency providers.

Each function here returns a concrete implementation of an abstract
Application-layer port, given a per-request DB session. This is
Dependency Injection made explicit via FastAPI's `Depends` mechanism --
routes never instantiate concrete repositories themselves (see
docs/adr/ADR-003).

Swapping to a different LLM provider or persistence technology means
changing only this file, never the use cases or the router's business logic.
"""
from __future__ import annotations

import os

from fastapi import Depends
from sqlalchemy.orm import Session

from procurement.application.ports.erp_gateway import ErpGateway
from procurement.application.ports.llm_adapter import LLMAdapter
from procurement.application.ports.repositories import (
    ApprovalRepository,
    CatalogItemRepository,
    CostCenterRepository,
    ProcurementRequestRepository,
    SupplierRepository,
    UserRepository,
)
from procurement.infrastructure.db import get_db_session
from procurement.infrastructure.mock_erp_gateway import MockErpGateway
from procurement.infrastructure.mock_llm_adapter import MockLLMAdapter
from procurement.infrastructure.repositories.sqlalchemy_approval_repository import (
    SqlAlchemyApprovalRepository,
)
from procurement.infrastructure.repositories.sqlalchemy_catalog_item_repository import (
    SqlAlchemyCatalogItemRepository,
)
from procurement.infrastructure.repositories.sqlalchemy_cost_center_repository import (
    SqlAlchemyCostCenterRepository,
)
from procurement.infrastructure.repositories.sqlalchemy_procurement_request_repository import (
    SqlAlchemyProcurementRequestRepository,
)
from procurement.infrastructure.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)
from procurement.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


def get_procurement_repository(
    session: Session = Depends(get_db_session),
) -> ProcurementRequestRepository:
    return SqlAlchemyProcurementRequestRepository(session)


def get_catalog_repository(
    session: Session = Depends(get_db_session),
) -> CatalogItemRepository:
    return SqlAlchemyCatalogItemRepository(session)


def get_supplier_repository(
    session: Session = Depends(get_db_session),
) -> SupplierRepository:
    return SqlAlchemySupplierRepository(session)


def get_cost_center_repository(
    session: Session = Depends(get_db_session),
) -> CostCenterRepository:
    return SqlAlchemyCostCenterRepository(session)


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_approval_repository(
    session: Session = Depends(get_db_session),
) -> ApprovalRepository:
    return SqlAlchemyApprovalRepository(session)


def get_llm_adapter() -> LLMAdapter:
    """Returns the mock adapter by default. Set USE_REAL_LLM=true (and wire
    a LiteLLM-backed adapter here) to switch -- see docs/PROJECT.md Future Work."""
    if os.environ.get("USE_REAL_LLM", "false").lower() == "true":
        raise NotImplementedError(
            "Real LLM adapter not yet implemented -- see docs/TASKS.md backlog."
        )
    return MockLLMAdapter()


_erp_gateway = MockErpGateway()


def get_erp_gateway() -> ErpGateway:
    """Mock ERP by default; a SAP-backed adapter would be returned here."""
    return _erp_gateway
