from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.application.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidOperationError,
)
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.application.services.balance_service import BalanceService
from app.application.services.idempotency_service import IdempotencyService
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


@dataclass(frozen=True, slots=True)
class TransferUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository
    balance_service: BalanceService
    idempotency_service: IdempotencyService

    def execute(
        self,
        *,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal | int | str,
        idempotency_key: str | None,
        transaction_id: UUID | str | None = None,
        timestamp: datetime | str | None = None,
    ) -> tuple[LedgerEntry, LedgerEntry]:
        idempotency_key = self.idempotency_service.ensure_unique_for_operation(
            idempotency_key=idempotency_key,
            transaction_id=transaction_id,
            account_id=f"{from_account_id}:{to_account_id}",
            timestamp=timestamp,
        )

        if from_account_id == to_account_id:
            raise InvalidOperationError("Transfer accounts must be different.")

        if self.account_repository.lock_by_id(from_account_id) is None:
            raise AccountNotFoundError("Source account not found.")

        if not self.account_repository.exists(to_account_id):
            raise AccountNotFoundError("Destination account not found.")

        money = Money.positive(amount)
        source_balance = self.balance_service.calculate(
            self.ledger_repository.get_by_account_id(from_account_id)
        )
        if source_balance.amount < money.amount:
            raise InsufficientFundsError("Insufficient funds.")

        debit_entry = LedgerEntry(
            account_id=from_account_id,
            transaction_type=TransactionType.DEBIT,
            amount=money,
            description=f"Transfer to account {to_account_id}",
            idempotency_key=idempotency_key,
        )
        credit_entry = LedgerEntry(
            account_id=to_account_id,
            transaction_type=TransactionType.CREDIT,
            amount=money,
            description=f"Transfer from account {from_account_id}",
            idempotency_key=idempotency_key,
        )

        self.ledger_repository.save_many([debit_entry, credit_entry])

        return debit_entry, credit_entry
