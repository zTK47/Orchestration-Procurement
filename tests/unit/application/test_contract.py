from decimal import Decimal

from procurement.application.contract import to_contract
from procurement.domain.entities import ApprovalLevel, ProcurementRequest
from procurement.domain.value_objects import SKU, Money, ParsedRequest


def _pending_request() -> ProcurementRequest:
    request = ProcurementRequest(
        id="req-123", requester_id="U-1", cost_center_id="CC-1",
        raw_text="I need 5 new Lenovo Laptop",
    )
    request.mark_parsed(ParsedRequest(5, "Lenovo Laptop", "Laptop", 0.95))
    request.mark_resolved(SKU("LEN-T14-G3"), "SUP-001", Money(Decimal("6000.00"), "CHF"))
    request.mark_validated()
    request.submit_for_approval([ApprovalLevel.MANAGER])
    return request


def test_contract_matches_the_agreed_shape_for_a_pending_request():
    contract = to_contract(_pending_request())

    assert contract["requestId"] == "req-123"
    assert contract["status"] == "PENDING_APPROVAL"
    assert contract["rawText"] == "I need 5 new Lenovo Laptop"
    assert contract["parsedData"] == {
        "quantity": 5, "productName": "Lenovo Laptop", "category": "Laptop", "confidence": 0.95,
    }
    assert contract["resolvedData"]["sku"] == "LEN-T14-G3"
    assert contract["resolvedData"]["supplierId"] == "SUP-001"
    assert contract["resolvedData"]["unitPrice"] == 1200.0
    assert contract["resolvedData"]["currency"] == "CHF"
    assert contract["validation"]["budgetCheck"] == "PASSED"
    assert contract["validation"]["stockCheck"] == "PASSED"
    assert contract["validation"]["requiresApproval"] is True
    assert contract["validation"]["approvalLevel"] == "MANAGER"
    assert contract["workflow"]["currentState"] == "PENDING_APPROVAL"
    assert contract["workflow"]["nextState"] == "APPROVED"
    assert contract["workflow"]["history"] == [
        "CREATED", "PARSED", "RESOLVED", "VALIDATED", "PENDING_APPROVAL",
    ]


def test_contract_of_a_new_request_has_empty_sections_and_a_next_state():
    request = ProcurementRequest(id="req-1", requester_id="U-1", cost_center_id="CC-1", raw_text="x")
    contract = to_contract(request)

    assert contract["parsedData"] is None
    assert contract["resolvedData"] is None
    assert contract["validation"]["requiresApproval"] is None
    assert contract["validation"]["approvalLevel"] is None
    assert contract["workflow"]["nextState"] == "PARSED"


def test_contract_reports_highest_level_and_all_levels():
    request = _pending_request()
    request.required_approval_levels = [ApprovalLevel.MANAGER, ApprovalLevel.BUDGET_OWNER]
    contract = to_contract(request)

    assert contract["validation"]["approvalLevel"] == "BUDGET_OWNER"
    assert contract["validation"]["approvalLevels"] == ["MANAGER", "BUDGET_OWNER"]
