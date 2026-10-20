"""OPO-UC-003 - see docs/specs/OPO-UC-003-validate-order-request.md"""
from __future__ import annotations

from order_pdf_orchestration.application.ports.repositories import (
    OrderRequestRepository,
    SupplierOfferRepository,
)
from order_pdf_orchestration.domain.entities import OrderRequest, OrderStatus
from order_pdf_orchestration.domain.exceptions import UnknownSupplierOfferError
from order_pdf_orchestration.domain.services.order_validation_rule import OrderValidationRule


class ValidateOrderRequestUseCase:
    def __init__(
        self,
        offer_repository: SupplierOfferRepository,
        order_repository: OrderRequestRepository,
        rule: OrderValidationRule | None = None,
    ) -> None:
        self._offers = offer_repository
        self._orders = order_repository
        self._rule = rule or OrderValidationRule()

    def execute(self, order: OrderRequest) -> OrderRequest:
        order.assert_can_transition_to(OrderStatus.VALIDATED)
        offer = self._offers.get_by_id(order.supplier_offer_id)
        if offer is None:
            raise UnknownSupplierOfferError(
                f"Supplier offer {order.supplier_offer_id} does not exist."
            )
        result = self._rule.evaluate(order, offer)
        if result.is_valid:
            order.mark_validated()
        else:
            order.mark_needs_clarification(result.notes)
        self._orders.save(order)
        return order
