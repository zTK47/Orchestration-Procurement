import pytest

from procurement.application.ports.llm_adapter import LLMAdapter
from procurement.application.use_cases.parse_request import ParseRequestUseCase
from procurement.domain.entities import ProcurementRequest, ProcurementStatus
from procurement.domain.value_objects import ParsedRequest
from procurement.infrastructure.in_memory_repositories import (
    InMemoryProcurementRequestRepository,
)


class StubLLMAdapter(LLMAdapter):
    """Fake LLM adapter returning a fixed response, used to test the use
    case in isolation from any real parsing logic."""

    def parse(self, raw_text: str) -> ParsedRequest:
        return ParsedRequest(quantity=5, product_name="Lenovo Laptop", category="Laptop", confidence=0.95)


def test_parse_request_advances_status_and_stores_parsed_data():
    repository = InMemoryProcurementRequestRepository()
    use_case = ParseRequestUseCase(llm_adapter=StubLLMAdapter(), procurement_repository=repository)
    request = ProcurementRequest(id="PR-1", requester_id="U-1", cost_center_id="CC-1", raw_text="I need 5 laptops")

    result = use_case.execute(request)

    assert result.status == ProcurementStatus.PARSED
    assert result.parsed_data.product_name == "Lenovo Laptop"
    assert repository.get_by_id("PR-1") is result


def test_parse_request_requires_raw_text():
    repository = InMemoryProcurementRequestRepository()
    use_case = ParseRequestUseCase(llm_adapter=StubLLMAdapter(), procurement_repository=repository)
    request = ProcurementRequest(id="PR-1", requester_id="U-1", cost_center_id="CC-1", raw_text=None)

    with pytest.raises(ValueError):
        use_case.execute(request)
