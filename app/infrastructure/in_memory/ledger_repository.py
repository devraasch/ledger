from uuid import UUID

from app.application.exceptions import DuplicateTransactionError
from app.application.repositories.ledger_repository import LedgerRepository
from app.domain.ledger_entry import LedgerEntry


class InMemoryLedgerRepository(LedgerRepository):
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._idempotency_keys: set[str] = set()

    def save(self, entry: LedgerEntry) -> None:
        if entry.idempotency_key in self._idempotency_keys:
            raise DuplicateTransactionError("Transaction already processed.")

        self._entries.append(entry)
        self._idempotency_keys.add(entry.idempotency_key)

    def get_by_account_id(self, account_id: UUID) -> list[LedgerEntry]:
        return [entry for entry in self._entries if entry.account_id == account_id]

    def exists_by_idempotency_key(self, idempotency_key: str) -> bool:
        return idempotency_key in self._idempotency_keys
