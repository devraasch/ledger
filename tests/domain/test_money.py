from decimal import Decimal

import pytest
from app.domain.money import Money


def test_create_valid_money() -> None:
    money = Money.of("10.50")

    assert money.amount == Decimal("10.50")


def test_money_does_not_accept_negative_amount() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        Money.of("-1")


def test_money_positive_does_not_accept_zero() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        Money.positive("0")


def test_sum_money() -> None:
    result = Money.of("10.50") + Money.of(5)

    assert result == Money.of("15.50")


def test_subtract_money() -> None:
    result = Money.of("10.50") - Money.of("2.25")

    assert result == Money.of("8.25")
