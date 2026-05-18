import os
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from app.application.services.balance_service import BalanceService
from app.application.services.idempotency_service import IdempotencyService
from app.application.use_cases.create_account import CreateAccountUseCase
from app.application.use_cases.deposit import DepositUseCase
from app.application.use_cases.get_balance import GetBalanceUseCase
from app.application.use_cases.get_statement import GetStatementUseCase
from app.application.use_cases.transfer import TransferUseCase
from app.application.use_cases.withdraw import WithdrawUseCase
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.in_memory.account_repository import InMemoryAccountRepository
from app.infrastructure.in_memory.ledger_repository import InMemoryLedgerRepository

REPOSITORY_BACKEND_ENV = "LEDGER_REPOSITORY_BACKEND"

_account_repository = InMemoryAccountRepository()
_ledger_repository = InMemoryLedgerRepository()
_balance_service = BalanceService()


def _use_database() -> bool:
    return os.getenv(REPOSITORY_BACKEND_ENV, "database") == "database"


def get_balance_service() -> BalanceService:
    return _balance_service


def get_create_account_use_case() -> Generator[CreateAccountUseCase]:
    if not _use_database():
        yield CreateAccountUseCase(_account_repository)
        return

    with SQLAlchemyUnitOfWork() as unit_of_work:
        yield CreateAccountUseCase(unit_of_work.accounts)


def get_deposit_use_case() -> Generator[DepositUseCase]:
    if not _use_database():
        idempotency_service = IdempotencyService(_ledger_repository)
        yield DepositUseCase(
            _account_repository,
            _ledger_repository,
            idempotency_service,
        )
        return

    with SQLAlchemyUnitOfWork() as unit_of_work:
        idempotency_service = IdempotencyService(unit_of_work.ledger)
        yield DepositUseCase(
            unit_of_work.accounts,
            unit_of_work.ledger,
            idempotency_service,
        )


def get_withdraw_use_case(
    balance_service: Annotated[BalanceService, Depends(get_balance_service)],
) -> Generator[WithdrawUseCase]:
    if not _use_database():
        idempotency_service = IdempotencyService(_ledger_repository)
        yield WithdrawUseCase(
            _account_repository,
            _ledger_repository,
            balance_service,
            idempotency_service,
        )
        return

    with SQLAlchemyUnitOfWork() as unit_of_work:
        idempotency_service = IdempotencyService(unit_of_work.ledger)
        yield WithdrawUseCase(
            unit_of_work.accounts,
            unit_of_work.ledger,
            balance_service,
            idempotency_service,
        )


def get_transfer_use_case(
    balance_service: Annotated[BalanceService, Depends(get_balance_service)],
) -> Generator[TransferUseCase]:
    if not _use_database():
        idempotency_service = IdempotencyService(_ledger_repository)
        yield TransferUseCase(
            _account_repository,
            _ledger_repository,
            balance_service,
            idempotency_service,
        )
        return

    with SQLAlchemyUnitOfWork() as unit_of_work:
        idempotency_service = IdempotencyService(unit_of_work.ledger)
        yield TransferUseCase(
            unit_of_work.accounts,
            unit_of_work.ledger,
            balance_service,
            idempotency_service,
        )


def get_balance_use_case(
    balance_service: Annotated[BalanceService, Depends(get_balance_service)],
) -> Generator[GetBalanceUseCase]:
    if not _use_database():
        yield GetBalanceUseCase(
            _account_repository,
            _ledger_repository,
            balance_service,
        )
        return

    with SQLAlchemyUnitOfWork() as unit_of_work:
        yield GetBalanceUseCase(
            unit_of_work.accounts,
            unit_of_work.ledger,
            balance_service,
        )


def get_statement_use_case() -> Generator[GetStatementUseCase]:
    if not _use_database():
        yield GetStatementUseCase(_account_repository, _ledger_repository)
        return

    with SQLAlchemyUnitOfWork() as unit_of_work:
        yield GetStatementUseCase(unit_of_work.accounts, unit_of_work.ledger)


def reset_in_memory_repositories() -> None:
    global _account_repository, _ledger_repository

    _account_repository = InMemoryAccountRepository()
    _ledger_repository = InMemoryLedgerRepository()
