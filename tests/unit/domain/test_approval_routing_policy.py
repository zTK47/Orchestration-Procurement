from decimal import Decimal

from procurement.domain.entities import ApprovalLevel
from procurement.domain.services.approval_routing_policy import ApprovalRoutingPolicy
from procurement.domain.value_objects import Money


def make_policy():
    return ApprovalRoutingPolicy(
        manager_threshold=Decimal(1000), budget_owner_threshold=Decimal(10000)
    )


def test_amount_at_or_below_manager_threshold_needs_no_approval():
    policy = make_policy()
    assert policy.required_levels(Money(Decimal(1000), "CHF")) == []
    assert policy.required_levels(Money(Decimal(500), "CHF")) == []


def test_amount_above_manager_threshold_needs_manager_approval():
    policy = make_policy()
    levels = policy.required_levels(Money(Decimal(5000), "CHF"))
    assert levels == [ApprovalLevel.MANAGER]


def test_amount_above_budget_owner_threshold_needs_both_approvals():
    policy = make_policy()
    levels = policy.required_levels(Money(Decimal(15000), "CHF"))
    assert levels == [ApprovalLevel.MANAGER, ApprovalLevel.BUDGET_OWNER]


def test_amount_exactly_at_budget_owner_threshold_needs_only_manager():
    policy = make_policy()
    levels = policy.required_levels(Money(Decimal(10000), "CHF"))
    assert levels == [ApprovalLevel.MANAGER]
