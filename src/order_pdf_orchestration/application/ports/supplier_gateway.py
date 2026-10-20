"""Port for handing an order (with its PDF) to the supplier."""
from __future__ import annotations

from abc import ABC, abstractmethod

from order_pdf_orchestration.domain.entities import OrderRequest, Supplier


class SupplierGatewayError(Exception):
    """The supplier could not be reached or rejected the order."""


class SupplierGateway(ABC):
    @abstractmethod
    def send_order(self, order: OrderRequest, supplier: Supplier) -> str:
        """Sends the order and its PDF; returns the supplier's order reference."""
