from decimal import Decimal

import pytest

from procurement.domain.value_objects import Money


def test_money_rejects_negative_amount():
    with pytest.raises(ValueError):
        Money(Decimal("-1.00"), "CHF")


def test_money_rejects_empty_currency():
    with pytest.raises(ValueError):
        Money(Decimal("10.00"), "")


def test_money_addition_same_currency():
    total = Money(Decimal("10.00"), "CHF") + Money(Decimal("5.00"), "CHF")
    assert total == Money(Decimal("15.00"), "CHF")


def test_money_operations_reject_mismatched_currency():
    with pytest.raises(ValueError):
        Money(Decimal("10.00"), "CHF") + Money(Decimal("5.00"), "EUR")


def test_money_comparison():
    assert Money(Decimal("20.00"), "CHF") > Money(Decimal("10.00"), "CHF")
    assert Money(Decimal("10.00"), "CHF") <= Money(Decimal("10.00"), "CHF")
