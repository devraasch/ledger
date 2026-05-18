from uuid import UUID

from app.application.repositories.account_repository import AccountRepository
from app.domain.account import Account


class InMemoryAccountRepository(AccountRepository):
    def __init__(self) -> None:
        self._accounts: dict[UUID, Account] = {}

    def save(self, account: Account) -> None:
        self._accounts[account.id] = account

    def get_by_id(self, account_id: UUID) -> Account | None:
        return self._accounts.get(account_id)

    def exists(self, account_id: UUID) -> bool:
        return account_id in self._accounts
