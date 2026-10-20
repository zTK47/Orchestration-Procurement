from decimal import Decimal

from procurement.application.use_cases.create_order import CreateOrderUseCase
from procurement.domain.entities import ApprovalLevel, ProcurementRequest, ProcurementStatus
from procurement.domain.services.approval_routing_policy import ApprovalRoutingPolicy
from procurement.domain.value_objects import SKU, Money, ParsedRequest
from procurement.infrastructure.in_memory_repositories import (
    InMemoryProcurementRequestRepository,
)


def validated_request(amount: str) -> ProcurementRequest:
    request = ProcurementRequest(id="PR-1", requester_id="U-1", cost_center_id="CC-1")
    request.mark_parsed(ParsedRequest(1, "Laptop", "Laptop", 0.9))
    request.mark_resolved(SKU("SKU-1"), "SUP-1", Money(Decimal(amount), "CHF"))
    request.mark_validated()
    return request


def test_small_amount_needs_no_approval_and_goes_straight_to_approved():
    use_case = CreateOrderUseCase(
        procurement_repository=InMemoryProcurementRequestRepository(),
        approval_routing_policy=ApprovalRoutingPolicy(Decimal(1000), Decimal(10000)),
    )
    request = validated_request("500")

    result = use_case.execute(request)

    assert result.status == ProcurementStatus.APPROVED
    assert result.required_approval_levels == []


def test_large_amount_requires_manager_approval_and_goes_pending():
    use_case = CreateOrderUseCase(
        procurement_repository=InMemoryProcurementRequestRepository(),
        approval_routing_policy=ApprovalRoutingPolicy(Decimal(1000), Decimal(10000)),
    )
    request = validated_request("5000")

    result = use_case.execute(request)

    assert result.status == ProcurementStatus.PENDING_APPROVAL
    assert result.required_approval_levels == [ApprovalLevel.MANAGER]


def test_very_large_amount_requires_both_approval_levels():
    use_case = CreateOrderUseCase(
        procurement_repository=InMemoryProcurementRequestRepository(),
        approval_routing_policy=ApprovalRoutingPolicy(Decimal(1000), Decimal(10000)),
    )
    request = validated_request("15000")

    result = use_case.execute(request)

    assert result.status == ProcurementStatus.PENDING_APPROVAL
    assert result.required_approval_levels == [ApprovalLevel.MANAGER, ApprovalLevel.BUDGET_OWNER]
