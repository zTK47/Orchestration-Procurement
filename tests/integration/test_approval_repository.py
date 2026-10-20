from datetime import UTC, datetime
from decimal import Decimal

from procurement.domain.entities import Approval, ApprovalDecision, ApprovalLevel
from procurement.infrastructure.models import CostCenterModel, ProcurementRequestModel, UserModel
from procurement.infrastructure.repositories.sqlalchemy_approval_repository import (
    SqlAlchemyApprovalRepository,
)


def _seed_parent_rows(db_session, user_ids: list[str], request_ids: list[str]) -> None:
    """ApprovalModel has NOT NULL foreign keys to users and
    procurement_requests -- seed minimal valid parent rows first so the FK
    constraints do not reject the insert."""
    db_session.add(
        CostCenterModel(id="CC-APR-TEST", name="Test CC", budget_total=Decimal(10000), budget_spent=Decimal(0))
    )
    for uid in user_ids:
        db_session.add(UserModel(id=uid, name=uid, email=f"{uid}@test.com", role="MANAGER"))
    for rid in request_ids:
        db_session.add(
            ProcurementRequestModel(
                id=rid, requester_id=user_ids[0], cost_center_id="CC-APR-TEST", status="PENDING_APPROVAL"
            )
        )
    db_session.commit()


def test_save_and_list_for_request(db_session):
    _seed_parent_rows(db_session, user_ids=["U-MAN-1"], request_ids=["PR-INT-1"])
    repository = SqlAlchemyApprovalRepository(db_session)

    approval = Approval(
        id="APR-INT-1",
        procurement_request_id="PR-INT-1",
        approver_id="U-MAN-1",
        level=ApprovalLevel.MANAGER,
        decision=ApprovalDecision.APPROVED,
        decided_at=datetime.now(UTC),
    )
    repository.save(approval)

    results = repository.list_for_request("PR-INT-1")

    assert len(results) == 1
    assert results[0].approver_id == "U-MAN-1"
    assert results[0].decision == ApprovalDecision.APPROVED


def test_list_for_request_only_returns_matching_requests(db_session):
    _seed_parent_rows(db_session, user_ids=["U-1", "U-2"], request_ids=["PR-A", "PR-B"])
    repository = SqlAlchemyApprovalRepository(db_session)

    repository.save(
        Approval(id="APR-INT-2", procurement_request_id="PR-A", approver_id="U-1", level=ApprovalLevel.MANAGER)
    )
    repository.save(
        Approval(id="APR-INT-3", procurement_request_id="PR-B", approver_id="U-2", level=ApprovalLevel.MANAGER)
    )

    results = repository.list_for_request("PR-A")

    assert len(results) == 1
    assert results[0].id == "APR-INT-2"


def test_list_for_request_returns_empty_for_unknown_request(db_session):
    repository = SqlAlchemyApprovalRepository(db_session)
    assert repository.list_for_request("does-not-exist") == []
