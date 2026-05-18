from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import AccountNotFoundError
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.application.services.balance_service import BalanceService
from app.domain.money import Money


@dataclass(frozen=True, slots=True)
class GetBalanceUseCase:
    account_repository: AccountRepository
    ledger_repository: LedgerRepository
    balance_service: BalanceService

    def execute(self, account_id: UUID) -> Money:
        if not self.account_repository.exists(account_id):
            raise AccountNotFoundError("Account not found.")

        entries = self.ledger_repository.get_by_account_id(account_id)
        return self.balance_service.calculate(entries)
