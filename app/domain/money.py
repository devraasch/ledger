from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Self


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError("Money amount cannot be negative.")

    @classmethod
    def of(cls, value: Decimal | int | str) -> Self:
        try:
            amount = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Money amount must be a valid decimal value.") from exc

        return cls(amount=amount)

    @classmethod
    def positive(cls, value: Decimal | int | str) -> Self:
        money = cls.of(value)
        money.ensure_positive()
        return money

    def ensure_positive(self) -> None:
        if self.amount <= Decimal("0"):
            raise ValueError("Money amount must be greater than zero.")

    def __add__(self, other: Self) -> Self:
        return Money.of(self.amount + other.amount)

    def __sub__(self, other: Self) -> Self:
        return Money.of(self.amount - other.amount)
