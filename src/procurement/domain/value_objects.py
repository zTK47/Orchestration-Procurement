"""Value Objects for the Procurement domain.

Rules:
- Pure Python only (no Pydantic, no ORM, no framework imports).
- Immutable (frozen dataclasses).
- Equality is based on value, not identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """An amount of money in a given currency.

    Invariants:
    - amount must not be negative.
    - currency is a non-empty ISO-like code (e.g. "CHF", "EUR").
    """

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative.")
        if not self.currency or not self.currency.strip():
            raise ValueError("Money currency must not be empty.")

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __gt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount >= other.amount

    def __lt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount <= other.amount

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} vs {other.currency}"
            )


@dataclass(frozen=True)
class SKU:
    """Stock Keeping Unit identifier for a catalog item."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("SKU value must not be empty.")


@dataclass(frozen=True)
class ParsedRequest:
    """Structured data extracted from a free-text procurement request.

    Produced by an LLM adapter (real or mocked) in the infrastructure layer,
    but the shape of this data is a domain concept, not an infrastructure one.
    """

    quantity: int
    product_name: str
    category: str
    confidence: float

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Parsed quantity must be a positive integer.")
        if not self.product_name or not self.product_name.strip():
            raise ValueError("Parsed product_name must not be empty.")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Parsed confidence must be between 0.0 and 1.0.")
