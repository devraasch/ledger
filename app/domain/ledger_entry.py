from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.money import Money
from app.domain.transaction_type import TransactionType


@dataclass(frozen=True, slots=True, kw_only=True)
class LedgerEntry:
    account_id: UUID
    transaction_type: TransactionType
    amount: Money
    description: str
    idempotency_key: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.amount.ensure_positive()

        idempotency_key = self.idempotency_key.strip()
        if not idempotency_key:
            raise ValueError("Ledger entry idempotency key is required.")

        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(self, "description", self.description.strip())
