from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.application.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
)
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.application.services.balance_service import BalanceService
from app.application.services.idempotency_service import IdempotencyService
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


@dataclass(frozen=True, slots=True)
class WithdrawUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository
    balance_service: BalanceService
    idempotency_service: IdempotencyService

    def execute(
        self,
        *,
        account_id: UUID,
        amount: Decimal | int | str,
        description: str,
        idempotency_key: str | None,
        transaction_id: UUID | str | None = None,
        timestamp: datetime | str | None = None,
    ) -> LedgerEntry:
        if self.account_repository.lock_by_id(account_id) is None:
            raise AccountNotFoundError("Account not found.")

        idempotency_key = self.idempotency_service.ensure_unique_for_operation(
            idempotency_key=idempotency_key,
            transaction_id=transaction_id,
            account_id=account_id,
            timestamp=timestamp,
        )

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
