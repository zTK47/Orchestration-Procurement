"""OPO-UC-006 - see docs/specs/OPO-UC-006-revise-order-line-items.md"""
from __future__ import annotations

from order_pdf_orchestration.application.ports.repositories import OrderRequestRepository
from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest


class ReviseOrderLineItemsUseCase:
    def __init__(self, order_repository: OrderRequestRepository) -> None:
        self._orders = order_repository

    def execute(self, order: OrderRequest, line_items: list[OrderLineItem]) -> OrderRequest:
        order.revise_line_items(line_items)
        self._orders.save(order)
        return order
