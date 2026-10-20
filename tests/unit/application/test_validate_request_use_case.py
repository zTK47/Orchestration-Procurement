from decimal import Decimal

import pytest

from procurement.application.use_cases.validate_request import ValidateRequestUseCase
from procurement.domain.entities import CostCenter, ProcurementRequest, ProcurementStatus
from procurement.domain.exceptions import BudgetExceededError
from procurement.domain.value_objects import SKU, Money, ParsedRequest
from procurement.infrastructure.in_memory_repositories import (
    InMemoryCostCenterRepository,
    InMemoryProcurementRequestRepository,
)


def resolved_request(amount: str) -> ProcurementRequest:
    request = ProcurementRequest(id="PR-1", requester_id="U-1", cost_center_id="CC-1")
    request.mark_parsed(ParsedRequest(1, "Laptop", "Laptop", 0.9))
    request.mark_resolved(SKU("SKU-1"), "SUP-1", Money(Decimal(amount), "CHF"))
    return request


def test_validate_within_budget_moves_to_validated_with_no_approval_decided_yet():
    cost_center = CostCenter(
        id="CC-1", name="IT", budget_total=Money(Decimal(50000), "CHF"), budget_spent=Money(Decimal(0), "CHF")
    )
    use_case = ValidateRequestUseCase(
        cost_center_repository=InMemoryCostCenterRepository([cost_center]),
        procurement_repository=InMemoryProcurementRequestRepository(),
    )
    request = resolved_request("5000")

    result = use_case.execute(request)

    assert result.status == ProcurementStatus.VALIDATED
    assert result.budget_check == "PASSED"
    assert result.required_approval_levels == []  # UC-003 does not decide this


def test_validate_exceeding_budget_raises_and_does_not_change_status():
    cost_center = CostCenter(
        id="CC-1", name="IT", budget_total=Money(Decimal(1000), "CHF"), budget_spent=Money(Decimal(900), "CHF")
    )
    use_case = ValidateRequestUseCase(
        cost_center_repository=InMemoryCostCenterRepository([cost_center]),
        procurement_repository=InMemoryProcurementRequestRepository(),
    )
    request = resolved_request("500")  # only 100 available

    with pytest.raises(BudgetExceededError):
        use_case.execute(request)

    assert request.status == ProcurementStatus.RESOLVED  # unchanged
