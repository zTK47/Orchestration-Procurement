"""OPO-UC-002 - see docs/specs/OPO-UC-002-generate-order-request.md"""
from __future__ import annotations

from order_pdf_orchestration.application.ports.order_generation_agent import (
    OrderGenerationAgent,
)
from order_pdf_orchestration.application.ports.repositories import (
    OrderRequestRepository,
    SupplierOfferRepository,
)
from order_pdf_orchestration.domain.entities import OrderRequest
from order_pdf_orchestration.domain.exceptions import UnknownSupplierOfferError


class GenerateOrderRequestUseCase:
    def __init__(
        self,
        agent: OrderGenerationAgent,
        offer_repository: SupplierOfferRepository,
        order_repository: OrderRequestRepository,
    ) -> None:
        self._agent = agent
        self._offers = offer_repository
        self._orders = order_repository

    def execute(self, order: OrderRequest) -> OrderRequest:
        order.assert_can_generate()
        offer = self._offers.get_by_id(order.supplier_offer_id)
        if offer is None:
            raise UnknownSupplierOfferError(
                f"Supplier offer {order.supplier_offer_id} does not exist."
            )
        line_items = self._agent.generate(order.prompt_text, offer)
        order.mark_generated(line_items)
        self._orders.save(order)
        return order
