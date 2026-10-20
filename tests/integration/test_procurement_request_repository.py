from decimal import Decimal

from procurement.domain.entities import ApprovalLevel, ProcurementRequest
from procurement.domain.value_objects import SKU, Money, ParsedRequest
from procurement.infrastructure.repositories.sqlalchemy_procurement_request_repository import (
    SqlAlchemyProcurementRequestRepository,
)


def _make_user_and_cost_center(db_session):
    """ProcurementRequestModel has FKs to users/cost_centers; insert minimal
    rows directly so the round-trip test is self-contained."""
    from procurement.infrastructure.models import CostCenterModel, UserModel

    db_session.add(UserModel(id="U-1", name="Alice", email="alice@test.com", role="REQUESTER"))
    db_session.add(
        CostCenterModel(id="CC-1", name="IT", budget_total=Decimal(50000), budget_spent=Decimal(0), currency="CHF")
    )
    db_session.commit()


def test_save_and_get_round_trip_preserves_all_fields(db_session):
    _make_user_and_cost_center(db_session)
    repository = SqlAlchemyProcurementRequestRepository(db_session)

    request = ProcurementRequest(id="PR-INTEGRATION-1", requester_id="U-1", cost_center_id="CC-1")
    request.mark_parsed(ParsedRequest(5, "Lenovo Laptop", "Laptop", 0.95))
    request.mark_resolved(SKU("LEN-T14-G3"), "SUP-001", Money(Decimal("6000.00"), "CHF"))
    request.mark_validated()
    request.submit_for_approval([ApprovalLevel.MANAGER])

    repository.save(request)

    reloaded = repository.get_by_id("PR-INTEGRATION-1")

    assert reloaded is not None
    assert reloaded.id == request.id
    assert reloaded.status == request.status
    assert reloaded.parsed_data == request.parsed_data
    assert reloaded.resolved_sku == request.resolved_sku
    assert reloaded.amount == request.amount
    assert reloaded.required_approval_levels == [ApprovalLevel.MANAGER]
    assert reloaded.history == request.history


def test_get_by_id_returns_none_for_unknown_id(db_session):
    repository = SqlAlchemyProcurementRequestRepository(db_session)
    assert repository.get_by_id("does-not-exist") is None


def test_save_updates_an_existing_row_rather_than_duplicating(db_session):
    _make_user_and_cost_center(db_session)
    repository = SqlAlchemyProcurementRequestRepository(db_session)

    request = ProcurementRequest(id="PR-INTEGRATION-2", requester_id="U-1", cost_center_id="CC-1")
    repository.save(request)

    request.mark_parsed(ParsedRequest(1, "Pen", "Office Supplies", 0.9))
    repository.save(request)

    reloaded = repository.get_by_id("PR-INTEGRATION-2")
    assert reloaded.parsed_data.product_name == "Pen"


def test_erp_reference_survives_a_round_trip(db_session):
    _make_user_and_cost_center(db_session)
    repository = SqlAlchemyProcurementRequestRepository(db_session)

    request = ProcurementRequest(id="PR-INTEGRATION-3", requester_id="U-1", cost_center_id="CC-1")
    request.mark_parsed(ParsedRequest(1, "Pen", "Pen", 0.9))
    request.mark_resolved(SKU("PEN-1"), "SUP-001", Money(Decimal("2.00"), "CHF"))
    request.mark_validated()
    request.submit_for_approval([])
    request.mark_order_sent("PO-TEST-1")
    repository.save(request)

    reloaded = repository.get_by_id("PR-INTEGRATION-3")

    assert reloaded.erp_reference == "PO-TEST-1"
    assert reloaded.status == request.status
