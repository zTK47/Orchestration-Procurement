from __future__ import annotations

from sqlalchemy.orm import Session

from procurement.application.ports.repositories import UserRepository
from procurement.domain.entities import User, UserRole
from procurement.infrastructure.models import UserModel


def _to_domain(model: UserModel) -> User:
    return User(id=model.id, name=model.name, email=model.email, role=UserRole(model.role))


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: str) -> User | None:
        model = self._session.get(UserModel, user_id)
        return _to_domain(model) if model else None
