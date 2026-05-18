import hashlib
import hmac
import os
from datetime import datetime
from uuid import UUID

from app.application.exceptions import DuplicateTransactionError
from app.application.repositories.ledger_repository import LedgerRepository

IDEMPOTENCY_SECRET_ENV = "IDEMPOTENCY_SECRET"


class IdempotencyService:
    def __init__(self, ledger_repository: LedgerRepository) -> None:
        self._ledger_repository = ledger_repository

    def ensure_unique(self, idempotency_key: str | None) -> str:
        key = self._normalize(idempotency_key)
        if self._ledger_repository.exists_by_idempotency_key(key):
            raise DuplicateTransactionError("Transaction already processed.")

        return key

    def ensure_unique_for_operation(
        self,
        *,
        idempotency_key: str | None,
        transaction_id: UUID | str | None,
        account_id: UUID | str,
        timestamp: datetime | str | None,
    ) -> str:
        key = idempotency_key
        if key is None:
            key = self.generate_key(
                transaction_id=transaction_id,
                account_id=account_id,
                timestamp=timestamp,
            )

        return self.ensure_unique(key)

    def generate_key(
        self,
        *,
        transaction_id: UUID | str | None,
        account_id: UUID | str,
        timestamp: datetime | str | None,
    ) -> str:
        if transaction_id is None:
            raise ValueError("Transaction id is required.")

        if timestamp is None:
            raise ValueError("Transaction timestamp is required.")

        message = "|".join(
            [
                str(transaction_id).strip(),
                str(account_id).strip(),
                self._normalize_timestamp(timestamp),
            ]
        )
        digest = hmac.new(
            self._secret(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"idem_{digest}"

    def _normalize(self, idempotency_key: str | None) -> str:
        if idempotency_key is None:
            raise ValueError("Idempotency key is required.")

        key = idempotency_key.strip()
        if not key:
            raise ValueError("Idempotency key is required.")

        return key

    def _normalize_timestamp(self, timestamp: datetime | str) -> str:
        if isinstance(timestamp, datetime):
            return timestamp.isoformat()

        value = timestamp.strip()
        if not value:
            raise ValueError("Transaction timestamp is required.")

        return value

    def _secret(self) -> bytes:
        return os.getenv(IDEMPOTENCY_SECRET_ENV, "ledger-development-secret").encode()
