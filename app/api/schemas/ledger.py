from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType


class MoneyOperationRequest(BaseModel):
    amount: str
    description: str
    idempotency_key: str


class TransferRequest(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    amount: str
    idempotency_key: str


class BalanceResponse(BaseModel):
    account_id: UUID
    balance: str

    @classmethod
    def from_money(cls, *, account_id: UUID, balance: Money) -> "BalanceResponse":
        return cls(account_id=account_id, balance=str(balance.amount))


class LedgerEntryResponse(BaseModel):
    id: UUID
    account_id: UUID
    transaction_type: TransactionType
    amount: str
    description: str
    created_at: datetime
    idempotency_key: str

    @classmethod
    def from_domain(cls, entry: LedgerEntry) -> "LedgerEntryResponse":
        return cls(
            id=entry.id,
            account_id=entry.account_id,
            transaction_type=entry.transaction_type,
            amount=str(entry.amount.amount),
            description=entry.description,
            created_at=entry.created_at,
            idempotency_key=entry.idempotency_key,
        )


class TransferResponse(BaseModel):
    debit_entry: LedgerEntryResponse
    credit_entry: LedgerEntryResponse


class StatementResponse(BaseModel):
    account_id: UUID
    entries: list[LedgerEntryResponse]
