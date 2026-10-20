"""OPO-UC-003 rules: at least one line item (rule 1) and every line item must be
found in the supplier offer (rule 2). A simple keyword check on purpose: anything
it cannot confirm goes to a human, it never approves on a guess."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest, SupplierOffer

_STOP_WORDS = {"a", "an", "the", "of", "for", "and", "with", "x", "pcs", "piece", "pieces"}


@dataclass(frozen=True)
class ValidationResult:
    notes: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.notes


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[\w-]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS]


def _keyword_in(keyword: str, offer_text: str) -> bool:
    if keyword in offer_text:
        return True
    return len(keyword) > 3 and keyword.endswith("s") and keyword[:-1] in offer_text


class OrderValidationRule:
    def evaluate(self, order: OrderRequest, offer: SupplierOffer) -> ValidationResult:
        if not order.line_items:
            return ValidationResult(["The order request has no line items."])
        offer_text = offer.raw_text.lower()
        notes = [
            f"Line item '{item.description}' does not match anything in the supplier offer."
            for item in order.line_items
            if not self._matches(item, offer_text)
        ]
        return ValidationResult(notes)

    @staticmethod
    def _matches(item: OrderLineItem, offer_text: str) -> bool:
        keywords = _keywords(item.description)
        return bool(keywords) and all(_keyword_in(k, offer_text) for k in keywords)
