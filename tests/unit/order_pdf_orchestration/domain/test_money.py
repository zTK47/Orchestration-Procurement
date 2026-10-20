from decimal import Decimal

import pytest

from order_pdf_orchestration.domain.value_objects import Money


def test_money_rejects_a_negative_amount():
    with pytest.raises(ValueError):
        Money(Decimal("-0.01"), "CHF")


def test_money_rejects_an_empty_currency():
    with pytest.raises(ValueError):
        Money(Decimal("1.00"), " ")


def test_money_adds_amounts_in_the_same_currency():
    assert Money(Decimal("1.50"), "CHF") + Money(Decimal("2.25"), "CHF") == Money(
        Decimal("3.75"), "CHF"
    )


def test_money_refuses_to_mix_currencies():
    with pytest.raises(ValueError):
        Money(Decimal(1), "CHF") + Money(Decimal(1), "EUR")


def test_money_times_a_quantity():
    assert Money(Decimal("89.90"), "CHF").times(3) == Money(Decimal("269.70"), "CHF")


def test_zero_money_in_a_currency():
    assert Money.zero("EUR") == Money(Decimal(0), "EUR")
