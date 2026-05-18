import os
from collections.abc import Callable, Generator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from uuid import uuid4

import pytest
from app.application.exceptions import InsufficientFundsError
from app.application.services.balance_service import BalanceService
from app.application.services.idempotency_service import IdempotencyService
from app.application.use_cases.create_account import CreateAccountUseCase
from app.application.use_cases.deposit import DepositUseCase
from app.application.use_cases.get_balance import GetBalanceUseCase
from app.application.use_cases.transfer import TransferUseCase
from app.application.use_cases.withdraw import WithdrawUseCase
from app.domain.account import Account
from app.domain.money import Money
from app.infrastructure.database.models import Base
from app.infrastructure.database.repositories import (
    SQLAlchemyAccountRepository,
    SQLAlchemyLedgerRepository,
)
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

CONCURRENCY_DATABASE_URL = os.getenv("CONCURRENCY_DATABASE_URL")


@dataclass(slots=True)
class UseCaseBundle:
    create_account: CreateAccountUseCase
    deposit: DepositUseCase
    withdraw: WithdrawUseCase
    transfer: TransferUseCase
    get_balance: GetBalanceUseCase
    session: Session

    def close(self) -> None:
        self.session.close()


@pytest.fixture(scope="module")
def session_factory() -> Generator[sessionmaker]:
    if CONCURRENCY_DATABASE_URL is None:
        pytest.skip("CONCURRENCY_DATABASE_URL is required for concurrency tests.")

    engine = create_engine(CONCURRENCY_DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is not available for concurrency tests: {exc}")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    yield factory

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def build_use_cases(
    session_factory: sessionmaker,
) -> Callable[[], UseCaseBundle]:
    def factory() -> UseCaseBundle:
        session = session_factory()
        account_repository = SQLAlchemyAccountRepository(session)
        ledger_repository = SQLAlchemyLedgerRepository(session)
        balance_service = BalanceService()
        idempotency_service = IdempotencyService(ledger_repository)
        return UseCaseBundle(
            create_account=CreateAccountUseCase(account_repository),
            deposit=DepositUseCase(
                account_repository,
                ledger_repository,
                idempotency_service,
            ),
            withdraw=WithdrawUseCase(
                account_repository,
                ledger_repository,
                balance_service,
                idempotency_service,
            ),
            transfer=TransferUseCase(
                account_repository,
                ledger_repository,
                balance_service,
                idempotency_service,
            ),
            get_balance=GetBalanceUseCase(
                account_repository,
                ledger_repository,
                balance_service,
            ),
            session=session,
        )

    return factory


def test_concurrent_withdraw_allows_only_one_debit(
    build_use_cases: Callable[[], UseCaseBundle],
) -> None:
    setup = build_use_cases()
    account = setup.create_account.execute("Concurrent Account")
    setup.deposit.execute(
        account_id=account.id,
        amount="100.00",
        description="Initial deposit",
        idempotency_key=f"deposit-{uuid4()}",
    )
    setup.close()

    def withdraw_money(idempotency_key: str) -> str:
        bundle = build_use_cases()
        try:
            bundle.withdraw.execute(
                account_id=account.id,
                amount="80.00",
                description="Concurrent withdrawal",
                idempotency_key=idempotency_key,
            )
            return "approved"
        except InsufficientFundsError:
            return "insufficient_funds"
        finally:
            bundle.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                withdraw_money,
                [f"withdraw-{uuid4()}", f"withdraw-{uuid4()}"],
            )
        )

    balance_bundle = build_use_cases()
    assert sorted(results) == ["approved", "insufficient_funds"]
    assert balance_bundle.get_balance.execute(account.id) == Money.of("20.00")
    balance_bundle.close()


def test_concurrent_transfer_allows_only_one_source_debit(
    build_use_cases: Callable[[], UseCaseBundle],
) -> None:
    setup = build_use_cases()
    source = setup.create_account.execute("Source Account")
    destination_a = setup.create_account.execute("Destination A")
    destination_b = setup.create_account.execute("Destination B")
    setup.deposit.execute(
        account_id=source.id,
        amount="100.00",
        description="Initial deposit",
        idempotency_key=f"deposit-{uuid4()}",
    )
    setup.close()

    def transfer_money(destination: Account) -> str:
        bundle = build_use_cases()
        try:
            bundle.transfer.execute(
                from_account_id=source.id,
                to_account_id=destination.id,
                amount="80.00",
                idempotency_key=f"transfer-{uuid4()}",
            )
            return str(destination.id)
        except InsufficientFundsError:
            return "insufficient_funds"
        finally:
            bundle.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                transfer_money,
                [destination_a, destination_b],
            )
        )

    balance_bundle = build_use_cases()
    destination_balances = [
        balance_bundle.get_balance.execute(destination_a.id),
        balance_bundle.get_balance.execute(destination_b.id),
    ]

    assert "insufficient_funds" in results
    assert balance_bundle.get_balance.execute(source.id) == Money.of("20.00")
    assert sorted(destination_balances, key=lambda money: money.amount) == [
        Money.of("0"),
        Money.of("80.00"),
    ]
    balance_bundle.close()
