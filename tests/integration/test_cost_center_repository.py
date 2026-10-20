from decimal import Decimal

from procurement.domain.entities import CostCenter
from procurement.domain.value_objects import Money
from procurement.infrastructure.repositories.sqlalchemy_cost_center_repository import (
    SqlAlchemyCostCenterRepository,
)


def test_cost_center_round_trip(db_session):
    repository = SqlAlchemyCostCenterRepository(db_session)
    cost_center = CostCenter(
        id="CC-INTEGRATION-1",
        name="IT Department",
        budget_total=Money(Decimal("50000.00"), "CHF"),
        budget_spent=Money(Decimal("0.00"), "CHF"),
    )

    repository.save(cost_center)
    reloaded = repository.get_by_id("CC-INTEGRATION-1")

    assert reloaded is not None
    assert reloaded.budget_total == cost_center.budget_total
    assert reloaded.budget_spent == cost_center.budget_spent


def test_cost_center_budget_spent_persists_after_update(db_session):
    repository = SqlAlchemyCostCenterRepository(db_session)
    cost_center = CostCenter(
        id="CC-INTEGRATION-2",
        name="Sales",
        budget_total=Money(Decimal("10000.00"), "CHF"),
        budget_spent=Money(Decimal("0.00"), "CHF"),
    )
    repository.save(cost_center)

    cost_center.spend(Money(Decimal("2500.00"), "CHF"))
    repository.save(cost_center)

    reloaded = repository.get_by_id("CC-INTEGRATION-2")
    assert reloaded.budget_spent == Money(Decimal("2500.00"), "CHF")
    assert reloaded.available_budget() == Money(Decimal("7500.00"), "CHF")


def test_get_by_id_returns_none_for_unknown_cost_center(db_session):
    repository = SqlAlchemyCostCenterRepository(db_session)
    assert repository.get_by_id("does-not-exist") is None
