"""SQLAlchemy implementation of ProcurementRequestRepository.

Maps between the pure-Python ProcurementRequest entity (domain layer) and
ProcurementRequestModel (SQLAlchemy ORM, infrastructure layer). The domain
never sees this mapping; it only knows the abstract port.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from procurement.application.ports.repositories import ProcurementRequestRepository
from procurement.domain.entities import (
    ApprovalLevel,
    ProcurementRequest,
    ProcurementStatus,
)
from procurement.domain.value_objects import SKU, Money, ParsedRequest
from procurement.infrastructure.models import ProcurementRequestModel


def _to_domain(model: ProcurementRequestModel) -> ProcurementRequest:
    request = ProcurementRequest(
        id=model.id,
        requester_id=model.requester_id,
        cost_center_id=model.cost_center_id,
        raw_text=model.raw_text,
        status=ProcurementStatus(model.status),
    )
    if model.parsed_quantity is not None:
        request.parsed_data = ParsedRequest(
            quantity=model.parsed_quantity,
            product_name=model.parsed_product_name,
            category=model.parsed_category,
            confidence=float(model.parsed_confidence),  # Numeric column -> Decimal from the driver
        )
    if model.resolved_sku is not None:
        request.resolved_sku = SKU(model.resolved_sku)
        request.resolved_supplier_id = model.resolved_supplier_id
    if model.amount is not None:
        request.amount = Money(Decimal(str(model.amount)), model.currency or "CHF")
    request.stock_check = model.stock_check
    request.erp_reference = model.erp_reference
    request.budget_check = model.budget_check
    request.required_approval_levels = [
        ApprovalLevel(lvl) for lvl in (model.required_approval_levels or "").split(",") if lvl
    ]
    request.history = [ProcurementStatus(s) for s in (model.history or model.status).split(",")]
    return request


def _apply_to_model(request: ProcurementRequest, model: ProcurementRequestModel) -> None:
    model.id = request.id
    model.requester_id = request.requester_id
    model.cost_center_id = request.cost_center_id
    model.raw_text = request.raw_text
    model.status = request.status.value
    if request.parsed_data:
        model.parsed_quantity = request.parsed_data.quantity
        model.parsed_product_name = request.parsed_data.product_name
        model.parsed_category = request.parsed_data.category
        model.parsed_confidence = request.parsed_data.confidence
    if request.resolved_sku:
        model.resolved_sku = request.resolved_sku.value
        model.resolved_supplier_id = request.resolved_supplier_id
    if request.amount:
        model.amount = request.amount.amount
        model.currency = request.amount.currency
    model.stock_check = request.stock_check
    model.erp_reference = request.erp_reference
    model.budget_check = request.budget_check
    model.required_approval_levels = ",".join(lvl.value for lvl in request.required_approval_levels)
    model.history = ",".join(s.value for s in request.history)


class SqlAlchemyProcurementRequestRepository(ProcurementRequestRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, request: ProcurementRequest) -> None:
        model = self._session.get(ProcurementRequestModel, request.id)
        if model is None:
            model = ProcurementRequestModel(id=request.id)
            self._session.add(model)
        _apply_to_model(request, model)
        self._session.commit()

    def get_by_id(self, request_id: str) -> ProcurementRequest | None:
        model = self._session.get(ProcurementRequestModel, request_id)
        return _to_domain(model) if model else None
