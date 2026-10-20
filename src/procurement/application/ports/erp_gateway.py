"""Port for the ERP integration (the whiteboard's ORDER_SENT / GOODS_RECEIPT
hand-off to an ERP such as SAP). The concrete adapter lives in infrastructure."""
from __future__ import annotations

from abc import ABC, abstractmethod

from procurement.domain.entities import ProcurementRequest


class ErpGatewayError(Exception):
    """The ERP could not be reached or rejected the call."""


class ErpGateway(ABC):
    @abstractmethod
    def send_purchase_order(self, request: ProcurementRequest) -> str:
        """Creates the purchase order in the ERP and returns its reference."""

    @abstractmethod
    def post_goods_receipt(self, erp_reference: str) -> None:
        """Books the goods receipt for an existing purchase order."""
