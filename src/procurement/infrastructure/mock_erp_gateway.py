"""Deterministic ERP stand-in: no network, records what it was asked to do."""
from __future__ import annotations

from procurement.application.ports.erp_gateway import ErpGateway
from procurement.domain.entities import ProcurementRequest


class MockErpGateway(ErpGateway):
    def __init__(self) -> None:
        self.sent_orders: list[str] = []
        self.goods_receipts: list[str] = []

    def send_purchase_order(self, request: ProcurementRequest) -> str:
        reference = f"PO-{request.id[:8].upper()}"
        self.sent_orders.append(reference)
        return reference

    def post_goods_receipt(self, erp_reference: str) -> None:
        self.goods_receipts.append(erp_reference)
