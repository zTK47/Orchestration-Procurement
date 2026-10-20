from decimal import Decimal

import pytest

from procurement.application.use_cases.record_approval_decision import (
    RecordApprovalDecisionUseCase,
)
from procurement.domain.entities import (
    ApprovalDecision,
    ApprovalLevel,
    CostCenter,
    ProcurementRequest,
    ProcurementStatus,
    User,
    UserRole,
)
from procurement.domain.exceptions import (
    BudgetExceededError,
    DuplicateApprovalError,
    IllegalStatusTransitionError,
    UnauthorizedApproverError,
)
from procurement.domain.value_objects import SKU, Money, ParsedRequest
from procurement.infrastructure.in_memory_repositories import (
    InMemoryApprovalRepository,
    InMemoryCostCenterRepository,
    InMemoryProcurementRequestRepository,
    InMemoryUserRepository,
)


def validated_request(amount: str, levels: list[ApprovalLevel]) -> ProcurementRequest:
    request = ProcurementRequest(id="PR-1", requester_id="U-REQ", cost_center_id="CC-1")
    request.mark_parsed(ParsedRequest(1, "Laptop", "Laptop", 0.9))
    request.mark_resolved(SKU("SKU-1"), "SUP-1", Money(Decimal(amount), "CHF"))
    request.mark_validated()
    request.submit_for_approval(levels)
    return request


def make_use_case(cost_center: CostCenter, users: list[User]):
    return RecordApprovalDecisionUseCase(
        procurement_repository=InMemoryProcurementRequestRepository(),
        approval_repository=InMemoryApprovalRepository(),
        cost_center_repository=InMemoryCostCenterRepository([cost_center]),
        user_repository=InMemoryUserRepository(users),
    )


def default_cost_center(total="50000", spent="0") -> CostCenter:
    return CostCenter(
        id="CC-1", name="IT", budget_total=Money(Decimal(total), "CHF"), budget_spent=Money(Decimal(spent), "CHF")
    )


def test_manager_approval_alone_approves_request_when_only_manager_required():
    manager = User(id="U-MAN", name="Bob", email="bob@x.com", role=UserRole.MANAGER)
    use_case = make_use_case(default_cost_center(), [manager])
    request = validated_request("5000", [ApprovalLevel.MANAGER])

    result = use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)

    assert result.status == ProcurementStatus.APPROVED


def test_request_stays_pending_until_all_required_levels_approve():
    manager = User(id="U-MAN", name="Bob", email="bob@x.com", role=UserRole.MANAGER)
    budget_owner = User(id="U-BO", name="Carla", email="carla@x.com", role=UserRole.BUDGET_OWNER)
    use_case = make_use_case(default_cost_center(), [manager, budget_owner])
    request = validated_request("15000", [ApprovalLevel.MANAGER, ApprovalLevel.BUDGET_OWNER])

    result = use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)
    assert result.status == ProcurementStatus.PENDING_APPROVAL  # still waiting for budget owner

    result = use_case.execute(request, "U-BO", ApprovalLevel.BUDGET_OWNER, ApprovalDecision.APPROVED)
    assert result.status == ProcurementStatus.APPROVED


def test_rejection_at_any_level_rejects_the_whole_request():
    manager = User(id="U-MAN", name="Bob", email="bob@x.com", role=UserRole.MANAGER)
    use_case = make_use_case(default_cost_center(), [manager])
    request = validated_request("5000", [ApprovalLevel.MANAGER])

    result = use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.REJECTED)

    assert result.status == ProcurementStatus.REJECTED


def test_unauthorized_role_cannot_approve_at_a_level():
    requester = User(id="U-REQ", name="Alice", email="alice@x.com", role=UserRole.REQUESTER)
    use_case = make_use_case(default_cost_center(), [requester])
    request = validated_request("5000", [ApprovalLevel.MANAGER])

    with pytest.raises(UnauthorizedApproverError):
        use_case.execute(request, "U-REQ", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)


def test_same_approver_cannot_approve_twice_at_the_same_level():
    manager = User(id="U-MAN", name="Bob", email="bob@x.com", role=UserRole.MANAGER)
    budget_owner = User(id="U-BO", name="Carla", email="carla@x.com", role=UserRole.BUDGET_OWNER)
    use_case = make_use_case(default_cost_center(), [manager, budget_owner])
    request = validated_request("15000", [ApprovalLevel.MANAGER, ApprovalLevel.BUDGET_OWNER])

    use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)

    with pytest.raises(DuplicateApprovalError):
        use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)


def test_final_approval_deducts_budget_from_cost_center():
    manager = User(id="U-MAN", name="Bob", email="bob@x.com", role=UserRole.MANAGER)
    cost_center = default_cost_center(total="50000", spent="1000")
    use_case = make_use_case(cost_center, [manager])
    request = validated_request("5000", [ApprovalLevel.MANAGER])

    use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)

    assert cost_center.budget_spent == Money(Decimal(6000), "CHF")


def test_final_approval_raises_if_budget_no_longer_sufficient():
    manager = User(id="U-MAN", name="Bob", email="bob@x.com", role=UserRole.MANAGER)
    # Budget was sufficient at validation time but has since been consumed elsewhere.
    cost_center = default_cost_center(total="5000", spent="4900")
    use_case = make_use_case(cost_center, [manager])
    request = validated_request("5000", [ApprovalLevel.MANAGER])

    with pytest.raises(BudgetExceededError):
        use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)


def test_decision_on_a_request_that_is_not_pending_is_rejected_and_not_stored():
    manager = User(id="U-MAN", name="Bob", email="bob@x.com", role=UserRole.MANAGER)
    approvals = InMemoryApprovalRepository()
    use_case = RecordApprovalDecisionUseCase(
        procurement_repository=InMemoryProcurementRequestRepository(),
        approval_repository=approvals,
        cost_center_repository=InMemoryCostCenterRepository([default_cost_center()]),
        user_repository=InMemoryUserRepository([manager]),
    )
    request = validated_request("500", [])  # auto-approved, no longer pending

    with pytest.raises(IllegalStatusTransitionError):
        use_case.execute(request, "U-MAN", ApprovalLevel.MANAGER, ApprovalDecision.APPROVED)

    assert approvals.list_for_request(request.id) == []
