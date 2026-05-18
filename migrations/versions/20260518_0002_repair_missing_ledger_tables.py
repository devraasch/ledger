"""repair missing ledger tables

Revision ID: 20260518_0002
Revises: 20260518_0001
Create Date: 2026-05-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260518_0002"
down_revision: str | Sequence[str] | None = "20260518_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "accounts" not in tables:
        op.create_table(
            "accounts",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("owner_name", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if "ledger_entries" not in tables:
        op.create_table(
            "ledger_entries",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("account_id", sa.Uuid(), nullable=False),
            sa.Column("transaction_type", sa.String(length=10), nullable=False),
            sa.Column("amount", sa.Numeric(18, 2), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("idempotency_key", sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "idempotency_key",
                "transaction_type",
                name="uq_ledger_entries_idempotency_key_transaction_type",
            ),
        )
        op.create_index(
            op.f("ix_ledger_entries_account_id"),
            "ledger_entries",
            ["account_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_ledger_entries_idempotency_key"),
            "ledger_entries",
            ["idempotency_key"],
            unique=False,
        )


def downgrade() -> None:
    pass
