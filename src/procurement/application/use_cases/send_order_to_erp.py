"""UC-007 - see docs/specs/UC-007-send-order-to-erp.md"""
from __future__ import annotations

from procurement.application.ports.erp_gateway import ErpGateway
from procurement.application.ports.repositories import ProcurementRequestRepository
from procurement.domain.entities import ProcurementRequest, ProcurementStatus


class SendOrderToErpUseCase:
    def __init__(
        self, erp_gateway: ErpGateway, procurement_repository: ProcurementRequestRepository
    ) -> None:
        self._erp_gateway = erp_gateway
        self._repository = procurement_repository

    def execute(self, request: ProcurementRequest) -> ProcurementRequest:
        request.assert_can_transition_to(ProcurementStatus.ORDER_SENT)
        reference = self._erp_gateway.send_purchase_order(request)
        request.mark_order_sent(reference)
        self._repository.save(request)
        return request
