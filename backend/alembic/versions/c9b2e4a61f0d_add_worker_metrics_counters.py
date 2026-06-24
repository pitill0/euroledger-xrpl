"""add worker metrics counters

Revision ID: c9b2e4a61f0d
Revises: 75a36d9956f0
Create Date: 2026-06-11 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9b2e4a61f0d"
down_revision: str | None = "75a36d9956f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "worker_states",
        sa.Column(
            "successful_cycles_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "failed_cycles_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "fetched_transactions_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "processed_transactions_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "skipped_transactions_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "failed_transactions_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "worker_states",
        "failed_transactions_total",
    )
    op.drop_column(
        "worker_states",
        "skipped_transactions_total",
    )
    op.drop_column(
        "worker_states",
        "processed_transactions_total",
    )
    op.drop_column(
        "worker_states",
        "fetched_transactions_total",
    )
    op.drop_column(
        "worker_states",
        "failed_cycles_total",
    )
    op.drop_column(
        "worker_states",
        "successful_cycles_total",
    )
