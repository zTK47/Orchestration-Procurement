import pytest


@pytest.fixture()
def opo_client(tmp_path):
    """The OPO app with fresh in-memory state per test (no database needed)."""
    from fastapi.testclient import TestClient

    from order_pdf_orchestration.infrastructure.in_memory_repositories import (
        InMemoryOrderRequestRepository,
        InMemorySupplierOfferRepository,
        InMemorySupplierRepository,
        default_suppliers,
    )
    from order_pdf_orchestration.infrastructure.main import create_app
    from order_pdf_orchestration.infrastructure.mock_document_renderer import MockDocumentRenderer
    from order_pdf_orchestration.infrastructure.mock_supplier_gateway import MockSupplierGateway
    from order_pdf_orchestration.interfaces.api import dependencies as deps

    suppliers = InMemorySupplierRepository(default_suppliers())
    offers = InMemorySupplierOfferRepository()
    orders = InMemoryOrderRequestRepository()
    renderer = MockDocumentRenderer(output_dir=tmp_path)
    gateway = MockSupplierGateway()

    app = create_app()
    app.dependency_overrides[deps.get_supplier_repository] = lambda: suppliers
    app.dependency_overrides[deps.get_offer_repository] = lambda: offers
    app.dependency_overrides[deps.get_order_repository] = lambda: orders
    app.dependency_overrides[deps.get_document_renderer] = lambda: renderer
    app.dependency_overrides[deps.get_supplier_gateway] = lambda: gateway

    with TestClient(app) as client:
        client.gateway = gateway
        yield client
