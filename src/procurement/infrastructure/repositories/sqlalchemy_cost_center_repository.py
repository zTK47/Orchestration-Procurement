from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from procurement.application.ports.repositories import CostCenterRepository
from procurement.domain.entities import CostCenter
from procurement.domain.value_objects import Money
from procurement.infrastructure.models import CostCenterModel


def _to_domain(model: CostCenterModel) -> CostCenter:
    return CostCenter(
        id=model.id,
        name=model.name,
        budget_total=Money(Decimal(str(model.budget_total)), model.currency),
        budget_spent=Money(Decimal(str(model.budget_spent)), model.currency),
    )


class SqlAlchemyCostCenterRepository(CostCenterRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, cost_center_id: str) -> CostCenter | None:
        model = self._session.get(CostCenterModel, cost_center_id)
        return _to_domain(model) if model else None

    def save(self, cost_center: CostCenter) -> None:
        model = self._session.get(CostCenterModel, cost_center.id)
        if model is None:
            model = CostCenterModel(id=cost_center.id)
            self._session.add(model)
        model.name = cost_center.name
        model.budget_total = cost_center.budget_total.amount
        model.budget_spent = cost_center.budget_spent.amount
        model.currency = cost_center.budget_total.currency
        self._session.commit()
