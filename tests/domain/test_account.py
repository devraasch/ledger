from datetime import UTC
from uuid import UUID

import pytest
from app.domain.account import Account


def test_create_account() -> None:
    account = Account(owner_name="Ada Lovelace")

    assert isinstance(account.id, UUID)
    assert account.owner_name == "Ada Lovelace"
    assert account.created_at.tzinfo is UTC


def test_account_requires_owner_name() -> None:
    with pytest.raises(ValueError, match="owner name is required"):
        Account(owner_name=" ")
