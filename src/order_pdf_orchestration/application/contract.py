"""Builds the JSON contract of the OPO API from domain objects.

Pure Python (no Pydantic): the HTTP schemas in interfaces/api mirror this shape.
"""
from __future__ import annotations

from order_pdf_orchestration.domain.entities import OrderRequest, SupplierOffer


def to_contract(order: OrderRequest) -> dict:
    total = order.total()
    next_state = order.next_state()
    return {
        "orderRequestId": order.id,
        "status": order.status.value,
        "supplierOfferId": order.supplier_offer_id,
        "promptText": order.prompt_text,
        "lineItems": [
            {
                "id": item.id,
                "description": item.description,
                "quantity": item.quantity,
                "unitPrice": float(item.unit_price.amount),
                "lineTotal": float(item.line_total().amount),
                "currency": item.unit_price.currency,
            }
            for item in order.line_items
        ],
        "total": None if total is None else {"amount": float(total.amount), "currency": total.currency},
        "validation": {"notes": list(order.validation_notes)},
        "pdfReference": order.pdf_reference,
        "supplierReference": order.supplier_reference,
        "workflow": {
            "currentState": order.status.value,
            "nextState": None if next_state is None else next_state.value,
            "history": [state.value for state in order.history],
        },
    }


def offer_to_contract(offer: SupplierOffer) -> dict:
    return {"offerId": offer.id, "supplierId": offer.supplier_id, "rawText": offer.raw_text}
