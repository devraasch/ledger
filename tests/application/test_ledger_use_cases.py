from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

import pytest
from app.application.exceptions import (
    AccountNotFoundError,
    DuplicateTransactionError,
    InsufficientFundsError,
)
from app.application.services.balance_service import BalanceService
from app.application.use_cases.create_account import CreateAccountUseCase
from app.application.use_cases.deposit import DepositUseCase
from app.application.use_cases.get_balance import GetBalanceUseCase
from app.application.use_cases.get_statement import GetStatementUseCase
from app.application.use_cases.transfer import TransferUseCase
from app.application.use_cases.withdraw import WithdrawUseCase
from app.domain.account import Account
from app.domain.money import Money
from app.domain.transaction_type import TransactionType
from app.infrastructure.in_memory.account_repository import InMemoryAccountRepository
from app.infrastructure.in_memory.ledger_repository import InMemoryLedgerRepository


@dataclass(frozen=True, slots=True)
class UseCaseContext:
    account_repository: InMemoryAccountRepository
    ledger_repository: InMemoryLedgerRepository
    create_account: CreateAccountUseCase
    deposit: DepositUseCase
    withdraw: WithdrawUseCase
    transfer: TransferUseCase
    get_balance: GetBalanceUseCase
    get_statement: GetStatementUseCase


@pytest.fixture
def context() -> UseCaseContext:
    account_repository = InMemoryAccountRepository()
    ledger_repository = InMemoryLedgerRepository()
    balance_service = BalanceService()

    return UseCaseContext(
        account_repository=account_repository,
        ledger_repository=ledger_repository,
        create_account=CreateAccountUseCase(account_repository),
        deposit=DepositUseCase(account_repository, ledger_repository),
        withdraw=WithdrawUseCase(
            account_repository,
            ledger_repository,
            balance_service,
        ),
        transfer=TransferUseCase(
            account_repository,
            ledger_repository,
            balance_service,
        ),
        get_balance=GetBalanceUseCase(
            account_repository,
            ledger_repository,
            balance_service,
        ),
        get_statement=GetStatementUseCase(account_repository, ledger_repository),
    )


def test_create_account(context: UseCaseContext) -> None:
    account = context.create_account.execute("Grace Hopper")

    assert isinstance(account, Account)
    assert account.owner_name == "Grace Hopper"
    assert context.account_repository.exists(account.id)


def test_deposit(context: UseCaseContext) -> None:
    account = context.create_account.execute("Grace Hopper")

    entry = context.deposit.execute(
        account_id=account.id,
        amount="100.00",
        description="Initial deposit",
        idempotency_key="deposit-001",
    )

    assert entry.transaction_type is TransactionType.CREDIT
    assert entry.amount == Money.of("100.00")
    assert context.get_balance.execute(account.id) == Money.of("100.00")


def test_deposit_requires_existing_account(context: UseCaseContext) -> None:
    with pytest.raises(AccountNotFoundError, match="Account not found"):
        context.deposit.execute(
            account_id=uuid4(),
            amount="100.00",
            description="Initial deposit",
            idempotency_key="deposit-001",
        )


def test_withdraw(context: UseCaseContext) -> None:
    account = context.create_account.execute("Grace Hopper")
    context.deposit.execute(
        account_id=account.id,
        amount="100.00",
        description="Initial deposit",
        idempotency_key="deposit-001",
    )

    entry = context.withdraw.execute(
        account_id=account.id,
        amount=Decimal("40.00"),
        description="Cash withdrawal",
        idempotency_key="withdraw-001",
    )

    assert entry.transaction_type is TransactionType.DEBIT
    assert entry.amount == Money.of("40.00")
    assert context.get_balance.execute(account.id) == Money.of("60.00")


def test_withdraw_does_not_allow_negative_balance(context: UseCaseContext) -> None:
    account = context.create_account.execute("Grace Hopper")

    with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
        context.withdraw.execute(
            account_id=account.id,
            amount="1.00",
            description="Cash withdrawal",
            idempotency_key="withdraw-001",
        )


def test_transfer(context: UseCaseContext) -> None:
    source = context.create_account.execute("Source Account")
    destination = context.create_account.execute("Destination Account")
    context.deposit.execute(
        account_id=source.id,
        amount="100.00",
        description="Initial deposit",
        idempotency_key="deposit-001",
    )

    debit_entry, credit_entry = context.transfer.execute(
        from_account_id=source.id,
        to_account_id=destination.id,
        amount="25.50",
        idempotency_key="transfer-001",
    )

    assert debit_entry.transaction_type is TransactionType.DEBIT
    assert credit_entry.transaction_type is TransactionType.CREDIT
    assert debit_entry.amount == Money.of("25.50")
    assert credit_entry.amount == Money.of("25.50")
    assert context.get_balance.execute(source.id) == Money.of("74.50")
    assert context.get_balance.execute(destination.id) == Money.of("25.50")


def test_transfer_does_not_allow_insufficient_funds(context: UseCaseContext) -> None:
    source = context.create_account.execute("Source Account")
    destination = context.create_account.execute("Destination Account")

    with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
        context.transfer.execute(
            from_account_id=source.id,
            to_account_id=destination.id,
            amount="10.00",
            idempotency_key="transfer-001",
        )


def test_get_balance_calculates_from_ledger(context: UseCaseContext) -> None:
    account = context.create_account.execute("Grace Hopper")
    context.deposit.execute(
        account_id=account.id,
        amount=100,
        description="Initial deposit",
        idempotency_key="deposit-001",
    )
    context.withdraw.execute(
        account_id=account.id,
        amount="35.25",
        description="Cash withdrawal",
        idempotency_key="withdraw-001",
    )

    balance = context.get_balance.execute(account.id)

    assert balance == Money.of("64.75")


def test_get_statement_returns_account_entries(context: UseCaseContext) -> None:
    account = context.create_account.execute("Grace Hopper")
    other_account = context.create_account.execute("Ada Lovelace")
    first_entry = context.deposit.execute(
        account_id=account.id,
        amount="100.00",
        description="Initial deposit",
        idempotency_key="deposit-001",
    )
    second_entry = context.withdraw.execute(
        account_id=account.id,
        amount="20.00",
        description="Cash withdrawal",
        idempotency_key="withdraw-001",
    )
    context.deposit.execute(
        account_id=other_account.id,
        amount="999.00",
        description="Other deposit",
        idempotency_key="deposit-002",
    )

    statement = context.get_statement.execute(account.id)

    assert statement == [first_entry, second_entry]


def test_prevent_duplicate_idempotency_key(context: UseCaseContext) -> None:
    account = context.create_account.execute("Grace Hopper")
    context.deposit.execute(
        account_id=account.id,
        amount="100.00",
        description="Initial deposit",
        idempotency_key="deposit-001",
    )

    with pytest.raises(DuplicateTransactionError, match="already processed"):
        context.deposit.execute(
            account_id=account.id,
            amount="100.00",
            description="Duplicated deposit",
            idempotency_key="deposit-001",
        )
