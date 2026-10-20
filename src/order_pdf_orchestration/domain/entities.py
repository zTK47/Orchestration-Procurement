"""Entities of the Order PDF Orchestration context. Pure Python, no frameworks."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from order_pdf_orchestration.domain.exceptions import (
    EmptyOrderRequestError,
    IllegalStatusTransitionError,
    InvalidLineItemError,
    InvalidSupplierOfferError,
    OrderNotValidatedError,
    PdfNotRenderedError,
)
from order_pdf_orchestration.domain.value_objects import Money


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    VALIDATED = "VALIDATED"
    SENT = "SENT"


_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.DRAFT: {OrderStatus.GENERATED},
    OrderStatus.GENERATED: {OrderStatus.VALIDATED, OrderStatus.NEEDS_CLARIFICATION},
    OrderStatus.NEEDS_CLARIFICATION: {OrderStatus.GENERATED},
    OrderStatus.VALIDATED: {OrderStatus.SENT},
    OrderStatus.SENT: set(),
}

_HAPPY_PATH_NEXT: dict[OrderStatus, OrderStatus | None] = {
    OrderStatus.DRAFT: OrderStatus.GENERATED,
    OrderStatus.GENERATED: OrderStatus.VALIDATED,
    OrderStatus.NEEDS_CLARIFICATION: OrderStatus.GENERATED,
    OrderStatus.VALIDATED: OrderStatus.SENT,
    OrderStatus.SENT: None,
}


@dataclass
class Supplier:
    id: str
    name: str
    contact_reference: str


@dataclass
class SupplierOffer:
    id: str
    supplier_id: str
    raw_text: str

    def __post_init__(self) -> None:
        if not self.raw_text or not self.raw_text.strip():
            raise InvalidSupplierOfferError("A supplier offer needs non-blank text.")


@dataclass(frozen=True)
class OrderLineItem:
    id: str
    description: str
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidLineItemError("Line item description must not be blank.")
        if self.quantity <= 0:
            raise InvalidLineItemError(
                f"Line item '{self.description}' must have a quantity greater than 0."
            )

    def line_total(self) -> Money:
        return self.unit_price.times(self.quantity)


@dataclass
class OrderRequest:
    """Aggregate root."""

    id: str
    supplier_offer_id: str
    prompt_text: str
    line_items: list[OrderLineItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.DRAFT
    validation_notes: list[str] = field(default_factory=list)
    pdf_reference: str | None = None
    supplier_reference: str | None = None
    history: list[OrderStatus] = field(default_factory=lambda: [OrderStatus.DRAFT])

    def assert_can_transition_to(self, new_status: OrderStatus) -> None:
        if new_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise IllegalStatusTransitionError(
                f"Cannot transition OrderRequest {self.id} from "
                f"{self.status.value} to {new_status.value}."
            )

    def transition_to(self, new_status: OrderStatus) -> None:
        self.assert_can_transition_to(new_status)
        self.status = new_status
        self.history.append(new_status)

    def next_state(self) -> OrderStatus | None:
        return _HAPPY_PATH_NEXT[self.status]

    def total(self) -> Money | None:
        if not self.line_items:
            return None
        total = Money.zero(self.line_items[0].unit_price.currency)
        for item in self.line_items:
            total = total + item.line_total()
        return total

    def assert_can_generate(self) -> None:
        """Agent generation only starts from DRAFT; NEEDS_CLARIFICATION goes back to
        GENERATED through revise_line_items (the human), never through the agent."""
        if self.status != OrderStatus.DRAFT:
            raise IllegalStatusTransitionError(
                f"OrderRequest {self.id} is {self.status.value}; only a DRAFT is generated."
            )

    def mark_generated(self, line_items: list[OrderLineItem]) -> None:
        self.assert_can_generate()
        self.line_items = list(line_items)
        self.transition_to(OrderStatus.GENERATED)

    def mark_validated(self) -> None:
        self.assert_can_transition_to(OrderStatus.VALIDATED)
        if not self.line_items:
            raise EmptyOrderRequestError(
                f"OrderRequest {self.id} has no line items and cannot be validated."
            )
        self.validation_notes = []
        self.transition_to(OrderStatus.VALIDATED)

    def mark_needs_clarification(self, notes: list[str]) -> None:
        self.assert_can_transition_to(OrderStatus.NEEDS_CLARIFICATION)
        self.validation_notes = list(notes)
        self.transition_to(OrderStatus.NEEDS_CLARIFICATION)

    def revise_line_items(self, line_items: list[OrderLineItem]) -> None:
        if self.status != OrderStatus.NEEDS_CLARIFICATION:
            raise IllegalStatusTransitionError(
                f"Line items of OrderRequest {self.id} can only be revised in "
                f"{OrderStatus.NEEDS_CLARIFICATION.value}, not {self.status.value}."
            )
        if not line_items:
            raise EmptyOrderRequestError("A revision needs at least one line item.")
        self.line_items = list(line_items)
        self.validation_notes = []
        self.transition_to(OrderStatus.GENERATED)

    def assert_can_attach_pdf(self) -> None:
        if self.status != OrderStatus.VALIDATED:
            raise OrderNotValidatedError(
                f"A PDF can only be rendered for a VALIDATED OrderRequest, "
                f"{self.id} is {self.status.value}."
            )

    def attach_pdf(self, pdf_reference: str) -> None:
        self.assert_can_attach_pdf()
        self.pdf_reference = pdf_reference

    def assert_can_send(self) -> None:
        self.assert_can_transition_to(OrderStatus.SENT)
        if self.pdf_reference is None:
            raise PdfNotRenderedError(
                f"OrderRequest {self.id} has no rendered PDF; render it before sending."
            )

    def mark_sent(self, supplier_reference: str) -> None:
        self.assert_can_send()
        self.supplier_reference = supplier_reference
        self.transition_to(OrderStatus.SENT)
