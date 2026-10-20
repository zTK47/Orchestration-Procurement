"""UC-004 - see docs/specs/UC-004-record-approval-decision.md"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from procurement.application.ports.repositories import (
    ApprovalRepository,
    CostCenterRepository,
    ProcurementRequestRepository,
    UserRepository,
)
from procurement.domain.entities import (
    Approval,
    ApprovalDecision,
    ApprovalLevel,
    ProcurementRequest,
    ProcurementStatus,
    UserRole,
)
from procurement.domain.exceptions import (
    BudgetExceededError,
    DuplicateApprovalError,
    IllegalStatusTransitionError,
    UnauthorizedApproverError,
)

# Which UserRole is allowed to decide at which ApprovalLevel.
_ROLE_FOR_LEVEL: dict[ApprovalLevel, UserRole] = {
    ApprovalLevel.MANAGER: UserRole.MANAGER,
    ApprovalLevel.BUDGET_OWNER: UserRole.BUDGET_OWNER,
}


class RecordApprovalDecisionUseCase:
    def __init__(
        self,
        procurement_repository: ProcurementRequestRepository,
        approval_repository: ApprovalRepository,
        cost_center_repository: CostCenterRepository,
        user_repository: UserRepository,
    ) -> None:
        self._procurement_repository = procurement_repository
        self._approval_repository = approval_repository
        self._cost_center_repository = cost_center_repository
        self._user_repository = user_repository

    def execute(
        self,
        request: ProcurementRequest,
        approver_id: str,
        level: ApprovalLevel,
        decision: ApprovalDecision,
    ) -> ProcurementRequest:
        if request.status != ProcurementStatus.PENDING_APPROVAL:
            raise IllegalStatusTransitionError(
                f"Request {request.id} is {request.status.value}, not PENDING_APPROVAL."
            )

        approver = self._user_repository.get_by_id(approver_id)
        if approver is None or approver.role != _ROLE_FOR_LEVEL[level]:
            raise UnauthorizedApproverError(
                f"User {approver_id} is not authorized to decide at level {level.value}."
            )

        existing = self._approval_repository.list_for_request(request.id)
        if any(
            a.approver_id == approver_id and a.level == level
            for a in existing
        ):
            raise DuplicateApprovalError(
                f"Approver {approver_id} already recorded a decision for "
                f"level {level.value} on request {request.id}."
            )

        approval = Approval(
            id=str(uuid.uuid4()),
            procurement_request_id=request.id,
            approver_id=approver_id,
            level=level,
            decision=decision,
            decided_at=datetime.now(UTC),
        )
        self._approval_repository.save(approval)

        if decision == ApprovalDecision.REJECTED:
            request.reject()
            self._procurement_repository.save(request)
            return request

        # decision == APPROVED: check whether every required level is now approved
        all_decisions = self._approval_repository.list_for_request(request.id)
        approved_levels = {
            a.level for a in all_decisions if a.decision == ApprovalDecision.APPROVED
        }
        still_pending = [
            lvl for lvl in request.required_approval_levels if lvl not in approved_levels
        ]

        if still_pending:
            # Not all required approvals are in yet; request stays PENDING_APPROVAL.
            return request

        # All required approvals are in: final, authoritative budget check.
        cost_center = self._cost_center_repository.get_by_id(request.cost_center_id)
        if cost_center is None:
            raise ValueError(f"Unknown cost center: {request.cost_center_id}")
        if request.amount is None:
            raise ValueError("Approved request has no resolved amount.")

        if not cost_center.has_available_budget(request.amount):
            raise BudgetExceededError(
                f"CostCenter {cost_center.id} no longer has enough budget "
                f"to approve request {request.id}."
            )

        cost_center.spend(request.amount)
        self._cost_center_repository.save(cost_center)
        request.approve()
        self._procurement_repository.save(request)
        return request
