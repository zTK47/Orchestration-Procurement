from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from procurement.application.ports.repositories import ApprovalRepository
from procurement.domain.entities import Approval, ApprovalDecision, ApprovalLevel
from procurement.infrastructure.models import ApprovalModel


def _to_domain(model: ApprovalModel) -> Approval:
    return Approval(
        id=model.id,
        procurement_request_id=model.procurement_request_id,
        approver_id=model.approver_id,
        level=ApprovalLevel(model.level),
        decision=ApprovalDecision(model.decision),
        decided_at=model.decided_at,
    )


class SqlAlchemyApprovalRepository(ApprovalRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, approval: Approval) -> None:
        model = self._session.get(ApprovalModel, approval.id) if approval.id else None
        if model is None:
            model = ApprovalModel(id=approval.id or str(uuid.uuid4()))
            self._session.add(model)
        model.procurement_request_id = approval.procurement_request_id
        model.approver_id = approval.approver_id
        model.level = approval.level.value
        model.decision = approval.decision.value
        model.decided_at = approval.decided_at
        self._session.commit()

    def list_for_request(self, procurement_request_id: str) -> list[Approval]:
        models = self._session.scalars(
            select(ApprovalModel).where(
                ApprovalModel.procurement_request_id == procurement_request_id
            )
        ).all()
        return [_to_domain(m) for m in models]
