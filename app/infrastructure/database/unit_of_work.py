from types import TracebackType

from sqlalchemy.orm import Session

from app.infrastructure.database.connection import session_factory
from app.infrastructure.database.repositories import (
    SQLAlchemyAccountRepository,
    SQLAlchemyLedgerRepository,
)


class SQLAlchemyUnitOfWork:
    def __init__(self) -> None:
        self.session: Session | None = None
        self.accounts: SQLAlchemyAccountRepository
        self.ledger: SQLAlchemyLedgerRepository

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = session_factory()
        self.accounts = SQLAlchemyAccountRepository(
            self.session,
            auto_commit=False,
        )
        self.ledger = SQLAlchemyLedgerRepository(
            self.session,
            auto_commit=False,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.session is None:
            return

        try:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
        finally:
            self.session.close()
