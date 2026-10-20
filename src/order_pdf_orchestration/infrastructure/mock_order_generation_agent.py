"""Deterministic stand-in for the order generation LLM/agent (ADR-007).

No model is called. A regex/keyword heuristic matches each requested item to a
line of the supplier offer. Its raw output is then schema-checked with Pydantic
before any domain object is built (ADR-008), exactly as a real LLM adapter must do.
An item the heuristic cannot match is kept with price 0 so that validation sends
the order to a human instead of silently dropping what was asked for.
"""
from __future__ import annotations

import re
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError

from order_pdf_orchestration.application.ports.order_generation_agent import (
    OrderGenerationAgent,
    OrderGenerationError,
)
from order_pdf_orchestration.domain.entities import OrderLineItem, SupplierOffer
from order_pdf_orchestration.domain.value_objects import Money

_PRICE = re.compile(
    r"(?:(?P<pre>CHF|EUR|USD)\s*(?P<a>\d[\d'’]*(?:[.,]\d{1,2})?))"
    r"|(?:(?P<b>\d[\d'’]*(?:[.,]\d{1,2})?)\s*(?P<post>CHF|EUR|USD))"
)
_FRAGMENT_SEPARATORS = re.compile(r",|;|\n|\band\b|\bplus\b", re.IGNORECASE)
_FILLER_WORDS = {
    "i", "we", "need", "want", "would", "like", "please", "order", "buy", "get", "to",
    "some", "of", "a", "an", "the", "new", "x", "pcs", "pieces", "units",
}
_DEFAULT_CURRENCY = "CHF"


class _AgentLineItem(BaseModel):
    description: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class _AgentOutput(BaseModel):
    line_items: list[_AgentLineItem]


class _OfferLine:
    def __init__(self, name: str, price: str, currency: str) -> None:
        self.name = name
        self.price = price
        self.currency = currency


def _offer_lines(offer_text: str) -> list[_OfferLine]:
    lines = []
    for raw_line in offer_text.splitlines():
        match = _PRICE.search(raw_line)
        if match is None:
            continue
        name = raw_line[: match.start()].strip(" -:,\t")
        if not name:
            continue
        amount = (match.group("a") or match.group("b")).replace("'", "").replace("’", "")
        if "," in amount and "." not in amount:
            amount = amount.replace(",", ".")
        lines.append(_OfferLine(name, amount, match.group("pre") or match.group("post")))
    return lines


def _keyword_in(keyword: str, text: str) -> bool:
    if keyword in text:
        return True
    return len(keyword) > 3 and keyword.endswith("s") and keyword[:-1] in text


class MockOrderGenerationAgent(OrderGenerationAgent):
    def generate(self, prompt_text: str, offer: SupplierOffer) -> list[OrderLineItem]:
        return self.to_line_items(self._raw_output(prompt_text, offer))

    def to_line_items(self, raw_output: dict) -> list[OrderLineItem]:
        try:
            output = _AgentOutput.model_validate(raw_output)
        except ValidationError as exc:
            raise OrderGenerationError(f"Agent output failed the schema check: {exc}") from exc
        return [
            OrderLineItem(
                id=f"LI-{number}",
                description=item.description,
                quantity=item.quantity,
                unit_price=Money(item.unit_price, item.currency),
            )
            for number, item in enumerate(output.line_items, start=1)
        ]

    def _raw_output(self, prompt_text: str, offer: SupplierOffer) -> dict:
        offer_lines = _offer_lines(offer.raw_text)
        currency = offer_lines[0].currency if offer_lines else _DEFAULT_CURRENCY
        items = []
        for fragment in _FRAGMENT_SEPARATORS.split(prompt_text):
            quantity_match = re.search(r"\b\d+\b", fragment)
            words = [
                w for w in re.findall(r"[\w'-]+", fragment)
                if w.lower() not in _FILLER_WORDS
                and not (quantity_match and w == quantity_match.group())
            ]
            if not words:
                continue
            quantity = int(quantity_match.group()) if quantity_match else 1
            match = self._best_offer_line(words, offer_lines)
            if match is None:
                items.append({"description": " ".join(words), "quantity": quantity,
                              "unit_price": "0", "currency": currency})
            else:
                items.append({"description": match.name, "quantity": quantity,
                              "unit_price": match.price, "currency": match.currency})
        return {"line_items": items}

    @staticmethod
    def _best_offer_line(words: list[str], offer_lines: list[_OfferLine]) -> _OfferLine | None:
        keywords = [w.lower() for w in words]
        for line in offer_lines:
            name = line.name.lower()
            if all(_keyword_in(k, name) for k in keywords):
                return line
        return None
