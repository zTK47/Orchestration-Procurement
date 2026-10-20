"""UC-003 - see docs/specs/UC-003-validate-request.md

Scope deliberately narrowed to match the original prompt: this use case only
checks the request's amount against the CostCenter's available budget. It
does NOT decide approval routing -- that is CreateOrderUseCase's job
(UC-004), so each use case has a single, testable responsibility.
"""
from __future__ import annotations

from procurement.application.ports.repositories import (
    CostCenterRepository,
    ProcurementRequestRepository,
)
from procurement.domain.entities import ProcurementRequest
from procurement.domain.exceptions import BudgetExceededError


class ValidateRequestUseCase:
    def __init__(
        self,
        cost_center_repository: CostCenterRepository,
        procurement_repository: ProcurementRequestRepository,
    ) -> None:
        self._cost_center_repository = cost_center_repository
        self._procurement_repository = procurement_repository

    def execute(self, request: ProcurementRequest) -> ProcurementRequest:
        if request.amount is None:
            raise ValueError("ProcurementRequest must be resolved before it can be validated.")

        cost_center = self._cost_center_repository.get_by_id(request.cost_center_id)
        if cost_center is None:
            raise ValueError(f"Unknown cost center: {request.cost_center_id}")

        if not cost_center.has_available_budget(request.amount):
            raise BudgetExceededError(
                f"CostCenter {cost_center.id} has insufficient budget for "
                f"amount {request.amount}."
            )

        request.mark_validated(budget_check="PASSED")
        self._procurement_repository.save(request)
        return request
