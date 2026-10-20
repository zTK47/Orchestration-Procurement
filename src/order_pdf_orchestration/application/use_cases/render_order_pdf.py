"""OPO-UC-004 - see docs/specs/OPO-UC-004-render-order-pdf.md"""
from __future__ import annotations

from order_pdf_orchestration.application.ports.document_renderer import DocumentRenderer
from order_pdf_orchestration.application.ports.repositories import (
    OrderRequestRepository,
    SupplierOfferRepository,
    SupplierRepository,
)
from order_pdf_orchestration.application.use_cases._supplier_lookup import supplier_of
from order_pdf_orchestration.domain.entities import OrderRequest


class RenderOrderPdfUseCase:
    def __init__(
        self,
        renderer: DocumentRenderer,
        supplier_repository: SupplierRepository,
        offer_repository: SupplierOfferRepository,
        order_repository: OrderRequestRepository,
    ) -> None:
        self._renderer = renderer
        self._suppliers = supplier_repository
        self._offers = offer_repository
        self._orders = order_repository

    def execute(self, order: OrderRequest) -> OrderRequest:
        order.assert_can_attach_pdf()
        supplier = supplier_of(order, self._offers, self._suppliers)
        order.attach_pdf(self._renderer.render(order, supplier))
        self._orders.save(order)
        return order
