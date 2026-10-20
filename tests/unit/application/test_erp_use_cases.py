from decimal import Decimal

import pytest

from procurement.application.ports.erp_gateway import ErpGateway, ErpGatewayError
from procurement.application.use_cases.complete_request import CompleteRequestUseCase
from procurement.application.use_cases.record_goods_receipt import RecordGoodsReceiptUseCase
from procurement.application.use_cases.send_order_to_erp import SendOrderToErpUseCase
from procurement.domain.entities import ProcurementRequest, ProcurementStatus
from procurement.domain.exceptions import IllegalStatusTransitionError
from procurement.domain.value_objects import SKU, Money, ParsedRequest
from procurement.infrastructure.in_memory_repositories import InMemoryProcurementRequestRepository
from procurement.infrastructure.mock_erp_gateway import MockErpGateway


class FailingErpGateway(ErpGateway):
    def send_purchase_order(self, request):
        raise ErpGatewayError("ERP unreachable")

    def post_goods_receipt(self, erp_reference):
        raise ErpGatewayError("ERP unreachable")


def approved_request() -> ProcurementRequest:
    request = ProcurementRequest(id="8f3a1c2d-0000", requester_id="U-1", cost_center_id="CC-1")
    request.mark_parsed(ParsedRequest(1, "Laptop", "Laptop", 0.9))
    request.mark_resolved(SKU("SKU-1"), "SUP-1", Money(Decimal("500.00"), "CHF"))
    request.mark_validated()
    request.submit_for_approval([])
    return request


def test_send_order_stores_erp_reference_and_moves_to_order_sent():
    gateway = MockErpGateway()
    use_case = SendOrderToErpUseCase(gateway, InMemoryProcurementRequestRepository())

    result = use_case.execute(approved_request())

    assert result.status == ProcurementStatus.ORDER_SENT
    assert result.erp_reference == "PO-8F3A1C2D"
    assert gateway.sent_orders == ["PO-8F3A1C2D"]


def test_send_order_before_approval_does_not_call_the_erp():
    gateway = MockErpGateway()
    use_case = SendOrderToErpUseCase(gateway, InMemoryProcurementRequestRepository())
    request = ProcurementRequest(id="r-1", requester_id="U-1", cost_center_id="CC-1")

    with pytest.raises(IllegalStatusTransitionError):
        use_case.execute(request)

    assert gateway.sent_orders == []


def test_send_order_leaves_status_unchanged_when_the_erp_fails():
    use_case = SendOrderToErpUseCase(FailingErpGateway(), InMemoryProcurementRequestRepository())
    request = approved_request()

    with pytest.raises(ErpGatewayError):
        use_case.execute(request)

    assert request.status == ProcurementStatus.APPROVED
    assert request.erp_reference is None


def test_goods_receipt_posts_to_erp_and_moves_to_goods_receipt():
    gateway = MockErpGateway()
    repository = InMemoryProcurementRequestRepository()
    request = SendOrderToErpUseCase(gateway, repository).execute(approved_request())

    result = RecordGoodsReceiptUseCase(gateway, repository).execute(request)

    assert result.status == ProcurementStatus.GOODS_RECEIPT
    assert gateway.goods_receipts == ["PO-8F3A1C2D"]


def test_goods_receipt_requires_a_sent_order():
    use_case = RecordGoodsReceiptUseCase(MockErpGateway(), InMemoryProcurementRequestRepository())

    with pytest.raises(IllegalStatusTransitionError):
        use_case.execute(approved_request())


def test_complete_request_after_goods_receipt():
    gateway = MockErpGateway()
    repository = InMemoryProcurementRequestRepository()
    request = SendOrderToErpUseCase(gateway, repository).execute(approved_request())
    request = RecordGoodsReceiptUseCase(gateway, repository).execute(request)

    result = CompleteRequestUseCase(repository).execute(request)

    assert result.status == ProcurementStatus.COMPLETED


def test_complete_request_before_goods_receipt_is_rejected():
    use_case = CompleteRequestUseCase(InMemoryProcurementRequestRepository())

    with pytest.raises(IllegalStatusTransitionError):
        use_case.execute(approved_request())
