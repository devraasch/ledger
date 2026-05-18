from datetime import UTC
from uuid import UUID, uuid4

import pytest
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


def test_create_ledger_entry() -> None:
    account_id = uuid4()

    entry = LedgerEntry(
        account_id=account_id,
        transaction_type=TransactionType.CREDIT,
        amount=Money.positive("100.00"),
        description="Initial deposit",
        idempotency_key="deposit-001",
    )

    assert isinstance(entry.id, UUID)
    assert entry.account_id == account_id
    assert entry.transaction_type is TransactionType.CREDIT
    assert entry.amount == Money.of("100.00")
    assert entry.description == "Initial deposit"
    assert entry.idempotency_key == "deposit-001"
    assert entry.created_at.tzinfo is UTC


def test_ledger_entry_requires_idempotency_key() -> None:
    with pytest.raises(ValueError, match="idempotency key is required"):
        LedgerEntry(
            account_id=uuid4(),
            transaction_type=TransactionType.CREDIT,
            amount=Money.positive("10.00"),
            description="Deposit",
            idempotency_key=" ",
        )


def test_ledger_entry_requires_positive_amount() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        LedgerEntry(
            account_id=uuid4(),
            transaction_type=TransactionType.DEBIT,
            amount=Money.of("0"),
            description="Debit",
            idempotency_key="debit-001",
        )
