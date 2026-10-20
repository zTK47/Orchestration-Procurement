"""Value objects of the Order PDF Orchestration context.

Money is re-implemented here on purpose instead of imported from
src/procurement: the two bounded contexts stay independent (docs/PROJECT.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative.")
        if not self.currency or not self.currency.strip():
            raise ValueError("Money currency must not be empty.")

    @classmethod
    def zero(cls, currency: str) -> Money:
        return cls(Decimal(0), currency)

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def times(self, quantity: int) -> Money:
        return Money(self.amount * quantity, self.currency)

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} vs {other.currency}"
            )
