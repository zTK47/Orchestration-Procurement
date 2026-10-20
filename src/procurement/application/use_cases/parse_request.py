"""UC-001 - see docs/specs/UC-001-parse-request.md"""
from __future__ import annotations

from procurement.application.ports.llm_adapter import LLMAdapter
from procurement.application.ports.repositories import ProcurementRequestRepository
from procurement.domain.entities import ProcurementRequest


class ParseRequestUseCase:
    def __init__(
        self,
        llm_adapter: LLMAdapter,
        procurement_repository: ProcurementRequestRepository,
    ) -> None:
        self._llm_adapter = llm_adapter
        self._repository = procurement_repository

    def execute(self, request: ProcurementRequest) -> ProcurementRequest:
        """Given a ProcurementRequest freshly created with `raw_text` set,
        parses it into structured data and advances its status to PARSED."""
        if not request.raw_text:
            raise ValueError("ProcurementRequest.raw_text must be set before parsing.")

        parsed_data = self._llm_adapter.parse(request.raw_text)
        request.mark_parsed(parsed_data)
        self._repository.save(request)
        return request
