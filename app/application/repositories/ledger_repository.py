from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.ledger_entry import LedgerEntry


class LedgerRepository(ABC):
    @abstractmethod
    def save(self, entry: LedgerEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_account_id(self, account_id: UUID) -> list[LedgerEntry]:
        raise NotImplementedError

    @abstractmethod
    def exists_by_idempotency_key(self, idempotency_key: str) -> bool:
        raise NotImplementedError
