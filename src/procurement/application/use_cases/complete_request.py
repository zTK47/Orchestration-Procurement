"""UC-009 - see docs/specs/UC-009-complete-request.md"""
from __future__ import annotations

from procurement.application.ports.repositories import ProcurementRequestRepository
from procurement.domain.entities import ProcurementRequest


class CompleteRequestUseCase:
    def __init__(self, procurement_repository: ProcurementRequestRepository) -> None:
        self._repository = procurement_repository

    def execute(self, request: ProcurementRequest) -> ProcurementRequest:
        request.complete()
        self._repository.save(request)
        return request
