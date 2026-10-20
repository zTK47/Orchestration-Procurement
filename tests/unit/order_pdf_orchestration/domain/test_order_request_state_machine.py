"""OrderRequest state machine, rule 1 (no VALIDATED without line items) and
rule 6 (SENT is terminal), plus the 'PDF before send' team decision."""
from decimal import Decimal

import pytest

from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest, OrderStatus
from order_pdf_orchestration.domain.exceptions import (
    EmptyOrderRequestError,
    IllegalStatusTransitionError,
    OrderNotValidatedError,
    PdfNotRenderedError,
)
from order_pdf_orchestration.domain.value_objects import Money


def item(description: str = "Dell Latitude 5440 Laptop") -> OrderLineItem:
    return OrderLineItem(id="LI-1", description=description, quantity=1, unit_price=Money(Decimal(10), "CHF"))


def draft() -> OrderRequest:
    return OrderRequest(id="OR-1", supplier_offer_id="OF-1", prompt_text="1 laptop")


def generated() -> OrderRequest:
    order = draft()
    order.mark_generated([item()])
    return order


def validated_with_pdf() -> OrderRequest:
    order = generated()
    order.mark_validated()
    order.attach_pdf("OR-1.pdf")
    return order


def sent() -> OrderRequest:
    order = validated_with_pdf()
    order.mark_sent("SUP-REF-1")
    return order


def test_new_order_request_starts_as_draft_with_history():
    order = draft()
    assert order.status == OrderStatus.DRAFT
    assert order.history == [OrderStatus.DRAFT]
    assert order.next_state() == OrderStatus.GENERATED


def test_happy_path_draft_generated_validated_sent():
    order = sent()
    assert order.status == OrderStatus.SENT
    assert order.supplier_reference == "SUP-REF-1"
    assert order.history == [
        OrderStatus.DRAFT, OrderStatus.GENERATED, OrderStatus.VALIDATED, OrderStatus.SENT,
    ]
    assert order.next_state() is None


def test_rule_1_cannot_validate_without_line_items():
    order = draft()
    order.mark_generated([])

    with pytest.raises(EmptyOrderRequestError):
        order.mark_validated()
    assert order.status == OrderStatus.GENERATED


def test_needs_clarification_keeps_notes_and_returns_to_generated_after_revision():
    order = generated()
    order.mark_needs_clarification(["'Unicorn' is not in the supplier offer."])
    assert order.status == OrderStatus.NEEDS_CLARIFICATION
    assert order.validation_notes == ["'Unicorn' is not in the supplier offer."]

    order.revise_line_items([item("HP EliteBook")])

    assert order.status == OrderStatus.GENERATED
    assert [i.description for i in order.line_items] == ["HP EliteBook"]
    assert order.validation_notes == []


def test_revision_needs_at_least_one_line_item():
    order = generated()
    order.mark_needs_clarification(["empty"])
    with pytest.raises(EmptyOrderRequestError):
        order.revise_line_items([])


def test_draft_cannot_skip_straight_to_validated():
    with pytest.raises(IllegalStatusTransitionError):
        draft().mark_validated()


def test_pdf_can_only_be_attached_to_a_validated_request():
    with pytest.raises(OrderNotValidatedError):
        generated().attach_pdf("x.pdf")


def test_cannot_send_without_a_rendered_pdf():
    order = generated()
    order.mark_validated()

    with pytest.raises(PdfNotRenderedError):
        order.mark_sent("SUP-REF-1")
    assert order.status == OrderStatus.VALIDATED


def test_cannot_send_a_request_that_is_not_validated():
    order = generated()
    with pytest.raises(IllegalStatusTransitionError):
        order.mark_sent("SUP-REF-1")


@pytest.mark.parametrize(
    "action",
    [
        lambda o: o.mark_generated([item()]),
        lambda o: o.mark_validated(),
        lambda o: o.mark_needs_clarification(["x"]),
        lambda o: o.revise_line_items([item()]),
        lambda o: o.mark_sent("SUP-REF-2"),
    ],
    ids=["regenerate", "revalidate", "clarify", "revise", "resend"],
)
def test_rule_6_sent_is_terminal(action):
    order = sent()
    with pytest.raises(IllegalStatusTransitionError):
        action(order)
    assert order.status == OrderStatus.SENT
    assert order.supplier_reference == "SUP-REF-1"


def test_agent_generation_is_only_for_drafts_not_a_way_around_human_revision():
    order = generated()
    order.mark_needs_clarification(["'Unicorn' is not in the supplier offer."])

    with pytest.raises(IllegalStatusTransitionError):
        order.mark_generated([item("Unicorn")])
    assert order.status == OrderStatus.NEEDS_CLARIFICATION
