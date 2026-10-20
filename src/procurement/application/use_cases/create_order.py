"""UC-004 - see docs/specs/UC-004-create-order.md

Matches the original prompt's `CreateOrderUseCase`: takes a VALIDATED
request and transitions it to PENDING_APPROVAL (or straight to APPROVED if
the amount is small enough to need no human approval), per rule 1 (approval
thresholds).
"""
from __future__ import annotations

from procurement.application.ports.repositories import ProcurementRequestRepository
from procurement.domain.entities import ProcurementRequest
from procurement.domain.services.approval_routing_policy import ApprovalRoutingPolicy


class CreateOrderUseCase:
    def __init__(
        self,
        procurement_repository: ProcurementRequestRepository,
        approval_routing_policy: ApprovalRoutingPolicy | None = None,
    ) -> None:
        self._procurement_repository = procurement_repository
        self._approval_routing_policy = approval_routing_policy or ApprovalRoutingPolicy()

    def execute(self, request: ProcurementRequest) -> ProcurementRequest:
        if request.amount is None:
            raise ValueError("ProcurementRequest must be validated before an order can be created.")

        required_levels = self._approval_routing_policy.required_levels(request.amount)
        request.submit_for_approval(required_levels)
        self._procurement_repository.save(request)
        return request
