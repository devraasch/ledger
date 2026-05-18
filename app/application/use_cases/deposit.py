from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.application.exceptions import AccountNotFoundError
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.application.services.idempotency_service import IdempotencyService
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


@dataclass(frozen=True, slots=True)
class DepositUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository
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
        if not self.account_repository.exists(account_id):
            raise AccountNotFoundError("Account not found.")

        idempotency_key = self.idempotency_service.ensure_unique_for_operation(
            idempotency_key=idempotency_key,
            transaction_id=transaction_id,
            account_id=account_id,
            timestamp=timestamp,
        )

        entry = LedgerEntry(
            account_id=account_id,
            transaction_type=TransactionType.CREDIT,
            amount=Money.positive(amount),
            description=description,
            idempotency_key=idempotency_key,
        )
        self.ledger_repository.save(entry)
        return entry
