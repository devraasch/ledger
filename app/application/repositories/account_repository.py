from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.account import Account


class AccountRepository(ABC):
    @abstractmethod
    def save(self, account: Account) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, account_id: UUID) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, account_id: UUID) -> bool:
        raise NotImplementedError
