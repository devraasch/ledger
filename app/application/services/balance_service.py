from collections.abc import Iterable

from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


class BalanceService:
    def calculate(self, entries: Iterable[LedgerEntry]) -> Money:
        balance = Money.of("0")

        for entry in entries:
            match entry.transaction_type:
                case TransactionType.CREDIT:
                    balance += entry.amount
                case TransactionType.DEBIT:
                    balance -= entry.amount

        return balance
