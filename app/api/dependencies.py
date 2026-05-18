from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.application.services.balance_service import BalanceService
from app.application.use_cases.create_account import CreateAccountUseCase
from app.application.use_cases.deposit import DepositUseCase
from app.application.use_cases.get_balance import GetBalanceUseCase
from app.application.use_cases.get_statement import GetStatementUseCase
from app.application.use_cases.transfer import TransferUseCase
from app.application.use_cases.withdraw import WithdrawUseCase
from app.infrastructure.in_memory.account_repository import InMemoryAccountRepository
from app.infrastructure.in_memory.ledger_repository import InMemoryLedgerRepository

_account_repository = InMemoryAccountRepository()
_ledger_repository = InMemoryLedgerRepository()
_balance_service = BalanceService()


def get_account_repository() -> AccountRepository:
    return _account_repository


def get_ledger_repository() -> LedgerRepository:
    return _ledger_repository


def get_balance_service() -> BalanceService:
    return _balance_service


def get_create_account_use_case() -> CreateAccountUseCase:
    return CreateAccountUseCase(get_account_repository())


def get_deposit_use_case() -> DepositUseCase:
    return DepositUseCase(get_account_repository(), get_ledger_repository())


def get_withdraw_use_case() -> WithdrawUseCase:
    return WithdrawUseCase(
        get_account_repository(),
        get_ledger_repository(),
        get_balance_service(),
    )


def get_transfer_use_case() -> TransferUseCase:
    return TransferUseCase(
        get_account_repository(),
        get_ledger_repository(),
        get_balance_service(),
    )


def get_balance_use_case() -> GetBalanceUseCase:
    return GetBalanceUseCase(
        get_account_repository(),
        get_ledger_repository(),
        get_balance_service(),
    )


def get_statement_use_case() -> GetStatementUseCase:
    return GetStatementUseCase(get_account_repository(), get_ledger_repository())


def reset_in_memory_repositories() -> None:
    global _account_repository, _ledger_repository

    _account_repository = InMemoryAccountRepository()
    _ledger_repository = InMemoryLedgerRepository()
