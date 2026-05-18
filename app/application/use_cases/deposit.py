from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.application.exceptions import AccountNotFoundError, DuplicateTransactionError
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


@dataclass(frozen=True, slots=True)
class DepositUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository

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

        entry = LedgerEntry(
            account_id=account_id,
            transaction_type=TransactionType.CREDIT,
            amount=Money.positive(amount),
            description=description,
            idempotency_key=idempotency_key,
        )
        self.ledger_repository.save(entry)
        return entry
