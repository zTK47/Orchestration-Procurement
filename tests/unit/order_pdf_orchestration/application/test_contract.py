"""JSON contract of the OPO API (mirrors application/contract.py in src/procurement)."""
from decimal import Decimal

from order_pdf_orchestration.application.contract import offer_to_contract, to_contract
from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest, SupplierOffer
from order_pdf_orchestration.domain.value_objects import Money


def test_contract_of_a_draft():
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="3 laptops")

    assert to_contract(order) == {
        "orderRequestId": "OR-1",
        "status": "DRAFT",
        "supplierOfferId": "OF-1",
        "promptText": "3 laptops",
        "lineItems": [],
        "total": None,
        "validation": {"notes": []},
        "pdfReference": None,
        "supplierReference": None,
        "workflow": {"currentState": "DRAFT", "nextState": "GENERATED", "history": ["DRAFT"]},
    }


def test_contract_lists_line_items_with_totals_and_notes():
    order = OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="3 laptops")
    order.mark_generated(
        [OrderLineItem(id="LI-1", description="Laptop", quantity=3, unit_price=Money(Decimal("1250.00"), "CHF"))]
    )
    order.mark_needs_clarification(["check the model"])

    body = to_contract(order)

    assert body["lineItems"] == [
        {"id": "LI-1", "description": "Laptop", "quantity": 3, "unitPrice": 1250.0,
         "lineTotal": 3750.0, "currency": "CHF"}
    ]
    assert body["total"] == {"amount": 3750.0, "currency": "CHF"}
    assert body["validation"] == {"notes": ["check the model"]}
    assert body["workflow"] == {
        "currentState": "NEEDS_CLARIFICATION",
        "nextState": "GENERATED",
        "history": ["DRAFT", "GENERATED", "NEEDS_CLARIFICATION"],
    }


def test_offer_contract():
    offer = SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text="Dock CHF 189")
    assert offer_to_contract(offer) == {"offerId": "OF-1", "supplierId": "SUP-1", "rawText": "Dock CHF 189"}
