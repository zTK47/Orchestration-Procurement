"""UC-008 - see docs/specs/UC-008-record-goods-receipt.md"""
from __future__ import annotations

from procurement.application.ports.erp_gateway import ErpGateway
from procurement.application.ports.repositories import ProcurementRequestRepository
from procurement.domain.entities import ProcurementRequest, ProcurementStatus


class RecordGoodsReceiptUseCase:
    def __init__(
        self, erp_gateway: ErpGateway, procurement_repository: ProcurementRequestRepository
    ) -> None:
        self._erp_gateway = erp_gateway
        self._repository = procurement_repository

    def execute(self, request: ProcurementRequest) -> ProcurementRequest:
        request.assert_can_transition_to(ProcurementStatus.GOODS_RECEIPT)
        self._erp_gateway.post_goods_receipt(request.erp_reference)
        request.mark_goods_received()
        self._repository.save(request)
        return request
