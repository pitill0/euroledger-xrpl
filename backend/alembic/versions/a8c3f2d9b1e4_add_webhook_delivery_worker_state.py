"""add webhook delivery worker state

Revision ID: a8c3f2d9b1e4
Revises: 9f1b2d3c4a5e
Create Date: 2026-06-19 16:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8c3f2d9b1e4"
down_revision: str | None = "9f1b2d3c4a5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "webhook_delivery_worker_states",
        sa.Column("worker_name", sa.String(length=100), nullable=False),
        sa.Column("last_cycle_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("successful_cycles_total", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("failed_cycles_total", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column(
            "processed_deliveries_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "delivered_deliveries_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("failed_deliveries_total", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column(
            "discarded_deliveries_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("worker_name"),
    )


def downgrade() -> None:
    op.drop_table("webhook_delivery_worker_states")
