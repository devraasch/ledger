from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.application.exceptions import (
    AccountNotFoundError,
    DuplicateTransactionError,
    InsufficientFundsError,
    InvalidOperationError,
)
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.application.services.balance_service import BalanceService
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


@dataclass(frozen=True, slots=True)
class TransferUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository
    balance_service: BalanceService

    def execute(
        self,
        *,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal | int | str,
        idempotency_key: str,
    ) -> tuple[LedgerEntry, LedgerEntry]:
        if from_account_id == to_account_id:
            raise InvalidOperationError("Transfer accounts must be different.")

        if not self.account_repository.exists(from_account_id):
            raise AccountNotFoundError("Source account not found.")

        if not self.account_repository.exists(to_account_id):
            raise AccountNotFoundError("Destination account not found.")

        debit_key = f"{idempotency_key}:debit"
        credit_key = f"{idempotency_key}:credit"
        if self.ledger_repository.exists_by_idempotency_key(
            debit_key
        ) or self.ledger_repository.exists_by_idempotency_key(credit_key):
            raise DuplicateTransactionError("Transaction already processed.")

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
            idempotency_key=debit_key,
        )
        credit_entry = LedgerEntry(
            account_id=to_account_id,
            transaction_type=TransactionType.CREDIT,
            amount=money,
            description=f"Transfer from account {from_account_id}",
            idempotency_key=credit_key,
        )

        self.ledger_repository.save(debit_entry)
        self.ledger_repository.save(credit_entry)

        return debit_entry, credit_entry
