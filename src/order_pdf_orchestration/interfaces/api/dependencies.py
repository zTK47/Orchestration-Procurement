"""FastAPI dependency providers: the one place where concrete adapters are chosen
for the OPO ports (same pattern as src/procurement/interfaces/api/dependencies.py).

This slice keeps state in memory for the lifetime of the process.
"""
from __future__ import annotations

import os

from order_pdf_orchestration.application.ports.document_renderer import DocumentRenderer
from order_pdf_orchestration.application.ports.order_generation_agent import (
    OrderGenerationAgent,
)
from order_pdf_orchestration.application.ports.repositories import (
    OrderRequestRepository,
    SupplierOfferRepository,
    SupplierRepository,
)
from order_pdf_orchestration.application.ports.supplier_gateway import SupplierGateway
from order_pdf_orchestration.infrastructure.in_memory_repositories import (
    InMemoryOrderRequestRepository,
    InMemorySupplierOfferRepository,
    InMemorySupplierRepository,
    default_suppliers,
)
from order_pdf_orchestration.infrastructure.mock_document_renderer import MockDocumentRenderer
from order_pdf_orchestration.infrastructure.mock_order_generation_agent import (
    MockOrderGenerationAgent,
)
from order_pdf_orchestration.infrastructure.mock_supplier_gateway import MockSupplierGateway

_suppliers = InMemorySupplierRepository(default_suppliers())
_offers = InMemorySupplierOfferRepository()
_orders = InMemoryOrderRequestRepository()
_renderer = MockDocumentRenderer(os.environ.get("ORDER_PDF_DIR"))
_gateway = MockSupplierGateway()


def get_supplier_repository() -> SupplierRepository:
    return _suppliers


def get_offer_repository() -> SupplierOfferRepository:
    return _offers


def get_order_repository() -> OrderRequestRepository:
    return _orders


def get_order_generation_agent() -> OrderGenerationAgent:
    """Mock by default (ADR-007). A real adapter would call the FHNW LiteLLM gateway
    with the key from an environment variable, never from the repository."""
    if os.environ.get("USE_REAL_LLM", "false").lower() == "true":
        raise NotImplementedError("Real order generation agent not implemented yet — see docs/TASKS.md.")
    return MockOrderGenerationAgent()


def get_document_renderer() -> DocumentRenderer:
    return _renderer


def get_supplier_gateway() -> SupplierGateway:
    return _gateway
