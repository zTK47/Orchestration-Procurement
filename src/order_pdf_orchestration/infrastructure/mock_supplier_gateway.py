"""Deterministic supplier stand-in: no network, records what it was asked to send."""
from __future__ import annotations

from order_pdf_orchestration.application.ports.supplier_gateway import SupplierGateway
from order_pdf_orchestration.domain.entities import OrderRequest, Supplier


class MockSupplierGateway(SupplierGateway):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str | None]] = []

    def send_order(self, order: OrderRequest, supplier: Supplier) -> str:
        self.sent.append((order.id, supplier.id, order.pdf_reference))
        return f"SUP-ORD-{order.id[:8].upper()}"
