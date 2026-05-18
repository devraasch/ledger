from collections.abc import Generator

import pytest
from app.application.exceptions import DuplicateTransactionError
from app.domain.account import Account
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType
from app.infrastructure.database.models import Base
from app.infrastructure.database.repositories import (
    SQLAlchemyAccountRepository,
    SQLAlchemyLedgerRepository,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with session_factory() as database_session:
        yield database_session

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_save_and_get_account_by_id(session: Session) -> None:
    repository = SQLAlchemyAccountRepository(session)
    account = Account(owner_name="Maria Silva")

    repository.save(account)

    persisted = repository.get_by_id(account.id)
    assert persisted == account


def test_account_exists(session: Session) -> None:
    repository = SQLAlchemyAccountRepository(session)
    account = Account(owner_name="Maria Silva")

    repository.save(account)

    assert repository.exists(account.id) is True


def test_lock_account_by_id(session: Session) -> None:
    repository = SQLAlchemyAccountRepository(session)
    account = Account(owner_name="Maria Silva")

    repository.save(account)

    assert repository.lock_by_id(account.id) == account


def test_save_and_get_ledger_entries_by_account(session: Session) -> None:
    account_repository = SQLAlchemyAccountRepository(session)
    ledger_repository = SQLAlchemyLedgerRepository(session)
    account = Account(owner_name="Maria Silva")
    account_repository.save(account)
    entry = LedgerEntry(
        account_id=account.id,
        transaction_type=TransactionType.CREDIT,
        amount=Money.positive("100.00"),
        description="Initial deposit",
        idempotency_key="deposit-001",
    )

    ledger_repository.save(entry)

    assert ledger_repository.get_by_account_id(account.id) == [entry]


def test_exists_by_idempotency_key(session: Session) -> None:
    account_repository = SQLAlchemyAccountRepository(session)
    ledger_repository = SQLAlchemyLedgerRepository(session)
    account = Account(owner_name="Maria Silva")
    account_repository.save(account)
    entry = LedgerEntry(
        account_id=account.id,
        transaction_type=TransactionType.CREDIT,
        amount=Money.positive("100.00"),
        description="Initial deposit",
        idempotency_key="deposit-001",
    )

    ledger_repository.save(entry)

    assert ledger_repository.exists_by_idempotency_key("deposit-001") is True
    assert ledger_repository.exists_by_idempotency_key("missing-key") is False


def test_duplicate_idempotency_key_for_same_entry_type_fails(
    session: Session,
) -> None:
    account_repository = SQLAlchemyAccountRepository(session)
    ledger_repository = SQLAlchemyLedgerRepository(session)
    account = Account(owner_name="Maria Silva")
    account_repository.save(account)
    first_entry = LedgerEntry(
        account_id=account.id,
        transaction_type=TransactionType.CREDIT,
        amount=Money.positive("100.00"),
        description="Initial deposit",
        idempotency_key="deposit-001",
    )
    duplicated_entry = LedgerEntry(
        account_id=account.id,
        transaction_type=TransactionType.CREDIT,
        amount=Money.positive("100.00"),
        description="Duplicated deposit",
        idempotency_key="deposit-001",
    )

    ledger_repository.save(first_entry)

    with pytest.raises(DuplicateTransactionError, match="already processed"):
        ledger_repository.save(duplicated_entry)


def test_transfer_entries_can_share_idempotency_key(session: Session) -> None:
    account_repository = SQLAlchemyAccountRepository(session)
    ledger_repository = SQLAlchemyLedgerRepository(session)
    source = Account(owner_name="Source Account")
    destination = Account(owner_name="Destination Account")
    account_repository.save(source)
    account_repository.save(destination)
    debit_entry = LedgerEntry(
        account_id=source.id,
        transaction_type=TransactionType.DEBIT,
        amount=Money.positive("25.00"),
        description="Transfer to destination",
        idempotency_key="transfer-001",
    )
    credit_entry = LedgerEntry(
        account_id=destination.id,
        transaction_type=TransactionType.CREDIT,
        amount=Money.positive("25.00"),
        description="Transfer from source",
        idempotency_key="transfer-001",
    )

    ledger_repository.save_many([debit_entry, credit_entry])

    assert ledger_repository.exists_by_idempotency_key("transfer-001") is True
    assert ledger_repository.get_by_account_id(source.id) == [debit_entry]
    assert ledger_repository.get_by_account_id(destination.id) == [credit_entry]
