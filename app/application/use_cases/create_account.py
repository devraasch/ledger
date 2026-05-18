from dataclasses import dataclass

from app.application.repositories.account_repository import AccountRepository
from app.domain.account import Account


@dataclass(frozen=True, slots=True)
class CreateAccountUseCase:
    account_repository: AccountRepository

    def execute(self, owner_name: str) -> Account:
        account = Account(owner_name=owner_name)
        self.account_repository.save(account)
        return account
