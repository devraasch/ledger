from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.application.exceptions import (
    AccountNotFoundError,
    DuplicateTransactionError,
    InsufficientFundsError,
)
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.application.services.balance_service import BalanceService
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


@dataclass(frozen=True, slots=True)
class WithdrawUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository
    balance_service: BalanceService

    def execute(
        self,
        *,
        account_id: UUID,
        amount: Decimal | int | str,
        description: str,
        idempotency_key: str,
    ) -> LedgerEntry:
        if not self.account_repository.exists(account_id):
            raise AccountNotFoundError("Account not found.")

        if self.ledger_repository.exists_by_idempotency_key(idempotency_key):
            raise DuplicateTransactionError("Transaction already processed.")

        money = Money.positive(amount)
        balance = self.balance_service.calculate(
            self.ledger_repository.get_by_account_id(account_id)
        )
        if balance.amount < money.amount:
            raise InsufficientFundsError("Insufficient funds.")

        entry = LedgerEntry(
            account_id=account_id,
            transaction_type=TransactionType.DEBIT,
            amount=money,
            description=description,
            idempotency_key=idempotency_key,
        )
        self.ledger_repository.save(entry)
        return entry
