"""Builds the JSON contract of the pipeline from a ProcurementRequest.

Pure Python (no Pydantic): shared by the HTTP layer and demo.py so both emit
the same shape. Fields beyond the original contract: resolvedData.totalAmount,
validation.approvalLevels and top-level erpReference.
"""
from __future__ import annotations

from procurement.domain.entities import ProcurementRequest


def to_contract(request: ProcurementRequest) -> dict:
    parsed = request.parsed_data
    unit_price = request.unit_price()
    next_state = request.next_state()
    return {
        "requestId": request.id,
        "status": request.status.value,
        "rawText": request.raw_text,
        "parsedData": None
        if parsed is None
        else {
            "quantity": parsed.quantity,
            "productName": parsed.product_name,
            "category": parsed.category,
            "confidence": parsed.confidence,
        },
        "resolvedData": None
        if request.resolved_sku is None or unit_price is None
        else {
            "sku": request.resolved_sku.value,
            "supplierId": request.resolved_supplier_id,
            "unitPrice": float(unit_price.amount),
            "totalAmount": float(request.amount.amount),
            "currency": unit_price.currency,
        },
        "validation": {
            "budgetCheck": request.budget_check,
            "stockCheck": request.stock_check,
            "requiresApproval": request.requires_approval(),
            "approvalLevel": None
            if request.highest_approval_level() is None
            else request.highest_approval_level().value,
            "approvalLevels": [level.value for level in request.required_approval_levels],
        },
        "workflow": {
            "currentState": request.status.value,
            "nextState": None if next_state is None else next_state.value,
            "history": [state.value for state in request.history],
        },
        "erpReference": request.erp_reference,
    }
