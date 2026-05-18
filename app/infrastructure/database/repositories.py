from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import DuplicateTransactionError
from app.application.repositories.account_repository import AccountRepository
from app.application.repositories.ledger_repository import LedgerRepository
from app.domain.account import Account
from app.domain.ledger_entry import LedgerEntry
from app.domain.money import Money
from app.domain.transaction_type import TransactionType
from app.infrastructure.database.models import AccountModel, LedgerEntryModel


class SQLAlchemyAccountRepository(AccountRepository):
    def __init__(self, session: Session, *, auto_commit: bool = True) -> None:
        self._session = session
        self._auto_commit = auto_commit

    def save(self, account: Account) -> None:
        self._session.add(
            AccountModel(
                id=account.id,
                owner_name=account.owner_name,
                created_at=account.created_at,
            )
        )
        self._commit_or_flush()

    def get_by_id(self, account_id: UUID) -> Account | None:
        model = self._session.get(AccountModel, account_id)
        if model is None:
            return None

        return Account(
            id=model.id,
            owner_name=model.owner_name,
            created_at=_ensure_utc(model.created_at),
        )

    def lock_by_id(self, account_id: UUID) -> Account | None:
        statement = (
            select(AccountModel).where(AccountModel.id == account_id).with_for_update()
        )
        model = self._session.scalars(statement).first()
        if model is None:
            return None

        return Account(
            id=model.id,
            owner_name=model.owner_name,
            created_at=_ensure_utc(model.created_at),
        )

    def exists(self, account_id: UUID) -> bool:
        statement = select(AccountModel.id).where(AccountModel.id == account_id)
        return self._session.execute(statement).first() is not None

    def _commit_or_flush(self) -> None:
        if self._auto_commit:
            self._session.commit()
            return

        self._session.flush()


class SQLAlchemyLedgerRepository(LedgerRepository):
    def __init__(self, session: Session, *, auto_commit: bool = True) -> None:
        self._session = session
        self._auto_commit = auto_commit

    def save(self, entry: LedgerEntry) -> None:
        self.save_many([entry])

    def save_many(self, entries: list[LedgerEntry]) -> None:
        self._session.add_all([self._to_model(entry) for entry in entries])
        try:
            self._commit_or_flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise DuplicateTransactionError("Transaction already processed.") from exc

    def get_by_account_id(self, account_id: UUID) -> list[LedgerEntry]:
        statement = (
            select(LedgerEntryModel)
            .where(LedgerEntryModel.account_id == account_id)
            .order_by(LedgerEntryModel.created_at, LedgerEntryModel.id)
        )
        entries = self._session.scalars(statement).all()
        return [self._to_domain(entry) for entry in entries]

    def exists_by_idempotency_key(self, idempotency_key: str) -> bool:
        statement = select(LedgerEntryModel.id).where(
            LedgerEntryModel.idempotency_key == idempotency_key
        )
        return self._session.execute(statement).first() is not None

    def _to_model(self, entry: LedgerEntry) -> LedgerEntryModel:
        return LedgerEntryModel(
            id=entry.id,
            account_id=entry.account_id,
            transaction_type=entry.transaction_type.value,
            amount=entry.amount.amount,
            description=entry.description,
            created_at=entry.created_at,
            idempotency_key=entry.idempotency_key,
        )

    def _to_domain(self, entry: LedgerEntryModel) -> LedgerEntry:
        return LedgerEntry(
            id=entry.id,
            account_id=entry.account_id,
            transaction_type=TransactionType(entry.transaction_type),
            amount=Money.of(entry.amount),
            description=entry.description,
            created_at=_ensure_utc(entry.created_at),
            idempotency_key=entry.idempotency_key,
        )

    def _commit_or_flush(self) -> None:
        if self._auto_commit:
            self._session.commit()
            return

        self._session.flush()


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value
