"""Determines which approval levels a ProcurementRequest requires, based on
its amount. See docs/specs/UC-003-validate-request.md.

Thresholds are deliberately kept as constructor parameters (not hardcoded
constants) so they can be configured per deployment/tests without touching
domain logic -- this keeps the policy itself pure and easily unit-testable.
"""
from __future__ import annotations

from decimal import Decimal

from procurement.domain.entities import ApprovalLevel
from procurement.domain.value_objects import Money


class ApprovalRoutingPolicy:
    def __init__(
        self,
        manager_threshold: Decimal = Decimal(1000),
        budget_owner_threshold: Decimal = Decimal(10000),
    ) -> None:
        self._manager_threshold = manager_threshold
        self._budget_owner_threshold = budget_owner_threshold

    def required_levels(self, amount: Money) -> list[ApprovalLevel]:
        """Rule:
        - amount <= manager_threshold                      -> no approval needed
        - manager_threshold < amount <= budget_owner_threshold -> MANAGER
        - amount > budget_owner_threshold                   -> MANAGER + BUDGET_OWNER
        """
        levels: list[ApprovalLevel] = []
        if amount.amount > self._manager_threshold:
            levels.append(ApprovalLevel.MANAGER)
        if amount.amount > self._budget_owner_threshold:
            levels.append(ApprovalLevel.BUDGET_OWNER)
        return levels
