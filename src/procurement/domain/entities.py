"""Domain entities for the Procurement Orchestrator.

Pure Python only: no Pydantic, no SQLAlchemy, no framework imports.
Entities have identity (an `id`) and encapsulate the business rules that
protect their own invariants.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from procurement.domain.exceptions import (
    IllegalStatusTransitionError,
)
from procurement.domain.value_objects import SKU, Money, ParsedRequest

# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class UserRole(str, Enum):
    REQUESTER = "REQUESTER"
    MANAGER = "MANAGER"
    BUDGET_OWNER = "BUDGET_OWNER"


class ProcurementStatus(str, Enum):
    CREATED = "CREATED"
    PARSED = "PARSED"
    RESOLVED = "RESOLVED"
    VALIDATED = "VALIDATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ORDER_SENT = "ORDER_SENT"
    GOODS_RECEIPT = "GOODS_RECEIPT"
    COMPLETED = "COMPLETED"


class ApprovalLevel(str, Enum):
    MANAGER = "MANAGER"
    BUDGET_OWNER = "BUDGET_OWNER"


class ApprovalDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# The workflow state machine (slide-documented in docs/PROJECT.md).
# Maps: current status -> set of statuses it may legally move to.
_ALLOWED_TRANSITIONS: dict[ProcurementStatus, set[ProcurementStatus]] = {
    ProcurementStatus.CREATED: {ProcurementStatus.PARSED},
    ProcurementStatus.PARSED: {ProcurementStatus.RESOLVED},
    ProcurementStatus.RESOLVED: {ProcurementStatus.VALIDATED},
    ProcurementStatus.VALIDATED: {
        ProcurementStatus.PENDING_APPROVAL,
        ProcurementStatus.APPROVED,  # auto-approved: no approval level required
    },
    ProcurementStatus.PENDING_APPROVAL: {
        ProcurementStatus.APPROVED,
        ProcurementStatus.REJECTED,
    },
    ProcurementStatus.APPROVED: {ProcurementStatus.ORDER_SENT},
    ProcurementStatus.ORDER_SENT: {ProcurementStatus.GOODS_RECEIPT},
    ProcurementStatus.GOODS_RECEIPT: {ProcurementStatus.COMPLETED},
    ProcurementStatus.REJECTED: set(),   # terminal
    ProcurementStatus.COMPLETED: set(),  # terminal
}

# Expected next status on the normal (happy) path, used to expose `nextState`.
_HAPPY_PATH_NEXT: dict[ProcurementStatus, ProcurementStatus | None] = {
    ProcurementStatus.CREATED: ProcurementStatus.PARSED,
    ProcurementStatus.PARSED: ProcurementStatus.RESOLVED,
    ProcurementStatus.RESOLVED: ProcurementStatus.VALIDATED,
    ProcurementStatus.VALIDATED: ProcurementStatus.PENDING_APPROVAL,
    ProcurementStatus.PENDING_APPROVAL: ProcurementStatus.APPROVED,
    ProcurementStatus.APPROVED: ProcurementStatus.ORDER_SENT,
    ProcurementStatus.ORDER_SENT: ProcurementStatus.GOODS_RECEIPT,
    ProcurementStatus.GOODS_RECEIPT: ProcurementStatus.COMPLETED,
    ProcurementStatus.REJECTED: None,
    ProcurementStatus.COMPLETED: None,
}

# Statuses in which approval routing has not been decided yet.
_BEFORE_APPROVAL_ROUTING = {
    ProcurementStatus.CREATED,
    ProcurementStatus.PARSED,
    ProcurementStatus.RESOLVED,
    ProcurementStatus.VALIDATED,
}


# --------------------------------------------------------------------------
# Entities
# --------------------------------------------------------------------------

@dataclass
class User:
    id: str
    name: str
    email: str
    role: UserRole


@dataclass
class CostCenter:
    id: str
    name: str
    budget_total: Money
    budget_spent: Money

    def available_budget(self) -> Money:
        return self.budget_total - self.budget_spent

    def has_available_budget(self, amount: Money) -> bool:
        return self.available_budget() >= amount

    def spend(self, amount: Money) -> None:
        """Adds `amount` to budget_spent. Callers check has_available_budget first."""
        self.budget_spent = self.budget_spent + amount


@dataclass
class Supplier:
    id: str
    name: str
    approved: bool


@dataclass
class CatalogItem:
    id: str
    sku: SKU
    product_name: str
    category: str
    supplier_id: str
    unit_price: Money
    stock_qty: int
    lead_time_days: int


@dataclass
class Approval:
    id: str
    procurement_request_id: str
    approver_id: str
    level: ApprovalLevel
    decision: ApprovalDecision = ApprovalDecision.PENDING
    decided_at: datetime | None = None


@dataclass
class ProcurementRequest:
    """Aggregate root. Every status change goes through `transition_to`."""

    id: str
    requester_id: str
    cost_center_id: str
    raw_text: str | None = None
    parsed_data: ParsedRequest | None = None
    resolved_sku: SKU | None = None
    resolved_supplier_id: str | None = None
    amount: Money | None = None
    stock_check: str | None = None
    budget_check: str | None = None
    required_approval_levels: list[ApprovalLevel] = field(default_factory=list)
    erp_reference: str | None = None
    status: ProcurementStatus = ProcurementStatus.CREATED
    history: list[ProcurementStatus] = field(
        default_factory=lambda: [ProcurementStatus.CREATED]
    )

    # -- state machine -----------------------------------------------------

    def assert_can_transition_to(self, new_status: ProcurementStatus) -> None:
        if new_status not in _ALLOWED_TRANSITIONS.get(self.status, set()):
            raise IllegalStatusTransitionError(
                f"Cannot transition ProcurementRequest {self.id} from "
                f"{self.status.value} to {new_status.value}."
            )

    def transition_to(self, new_status: ProcurementStatus) -> None:
        self.assert_can_transition_to(new_status)
        self.status = new_status
        self.history.append(new_status)

    def next_state(self) -> ProcurementStatus | None:
        return _HAPPY_PATH_NEXT.get(self.status)

    # -- derived values ----------------------------------------------------

    def unit_price(self) -> Money | None:
        if self.amount is None or self.parsed_data is None:
            return None
        return Money(
            (self.amount.amount / self.parsed_data.quantity).quantize(Decimal("0.01")),
            self.amount.currency,
        )

    def requires_approval(self) -> bool | None:
        """None until approval routing has been decided (see CreateOrderUseCase)."""
        if self.status in _BEFORE_APPROVAL_ROUTING:
            return None
        return bool(self.required_approval_levels)

    def highest_approval_level(self) -> ApprovalLevel | None:
        return self.required_approval_levels[-1] if self.required_approval_levels else None

    # -- pipeline steps ----------------------------------------------------

    def mark_parsed(self, parsed_data: ParsedRequest) -> None:
        self.parsed_data = parsed_data
        self.transition_to(ProcurementStatus.PARSED)

    def mark_resolved(
        self, sku: SKU, supplier_id: str, amount: Money, stock_check: str = "PASSED"
    ) -> None:
        self.resolved_sku = sku
        self.resolved_supplier_id = supplier_id
        self.amount = amount
        self.stock_check = stock_check
        self.transition_to(ProcurementStatus.RESOLVED)

    def mark_validated(self, budget_check: str = "PASSED") -> None:
        """Budget check only; approval routing is decided in submit_for_approval."""
        self.budget_check = budget_check
        self.transition_to(ProcurementStatus.VALIDATED)

    def submit_for_approval(self, required_approval_levels: list[ApprovalLevel]) -> None:
        self.required_approval_levels = required_approval_levels
        if required_approval_levels:
            self.transition_to(ProcurementStatus.PENDING_APPROVAL)
        else:
            self.transition_to(ProcurementStatus.APPROVED)

    def approve(self) -> None:
        self.transition_to(ProcurementStatus.APPROVED)

    def reject(self) -> None:
        self.transition_to(ProcurementStatus.REJECTED)

    def mark_order_sent(self, erp_reference: str) -> None:
        self.assert_can_transition_to(ProcurementStatus.ORDER_SENT)
        self.erp_reference = erp_reference
        self.transition_to(ProcurementStatus.ORDER_SENT)

    def mark_goods_received(self) -> None:
        self.transition_to(ProcurementStatus.GOODS_RECEIPT)

    def complete(self) -> None:
        self.transition_to(ProcurementStatus.COMPLETED)
