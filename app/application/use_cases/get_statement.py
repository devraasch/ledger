from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import AccountNotFoundError
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.domain.ledger_entry import LedgerEntry


@dataclass(frozen=True, slots=True)
class GetStatementUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository

    def execute(self, account_id: UUID) -> list[LedgerEntry]:
        if not self.account_repository.exists(account_id):
            raise AccountNotFoundError("Account not found.")

        return self.ledger_repository.get_by_account_id(account_id)
