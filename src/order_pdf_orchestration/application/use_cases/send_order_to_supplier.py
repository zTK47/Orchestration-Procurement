"""OPO-UC-005 - see docs/specs/OPO-UC-005-send-order-to-supplier.md"""
from __future__ import annotations

from order_pdf_orchestration.application.ports.repositories import (
    OrderRequestRepository,
    SupplierOfferRepository,
    SupplierRepository,
)
from order_pdf_orchestration.application.ports.supplier_gateway import SupplierGateway
from order_pdf_orchestration.application.use_cases._supplier_lookup import supplier_of
from order_pdf_orchestration.domain.entities import OrderRequest


class SendOrderToSupplierUseCase:
    def __init__(
        self,
        gateway: SupplierGateway,
        supplier_repository: SupplierRepository,
        offer_repository: SupplierOfferRepository,
        order_repository: OrderRequestRepository,
    ) -> None:
        self._gateway = gateway
        self._suppliers = supplier_repository
        self._offers = offer_repository
        self._orders = order_repository

    def execute(self, order: OrderRequest) -> OrderRequest:
        order.assert_can_send()
        supplier = supplier_of(order, self._offers, self._suppliers)
        order.mark_sent(self._gateway.send_order(order, supplier))
        self._orders.save(order)
        return order
