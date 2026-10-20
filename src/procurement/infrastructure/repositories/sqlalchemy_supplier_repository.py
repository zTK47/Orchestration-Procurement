from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from procurement.application.ports.repositories import SupplierRepository
from procurement.domain.entities import Supplier
from procurement.infrastructure.models import SupplierModel


def _to_domain(model: SupplierModel) -> Supplier:
    return Supplier(id=model.id, name=model.name, approved=model.approved)


class SqlAlchemySupplierRepository(SupplierRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all_by_id(self) -> dict[str, Supplier]:
        models = self._session.scalars(select(SupplierModel)).all()
        return {m.id: _to_domain(m) for m in models}
