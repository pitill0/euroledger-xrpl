"""add payment intent expiration

Revision ID: 541c7e6496cd
Revises: c9b2e4a61f0d
Create Date: 2026-06-11 15:53:16.103258

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "541c7e6496cd"
down_revision: str | None = "c9b2e4a61f0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "payment_intents",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE payment_intents
        SET expires_at = created_at + INTERVAL '15 minutes'
        WHERE expires_at IS NULL
        """
    )

    op.alter_column(
        "payment_intents",
        "expires_at",
        nullable=False,
    )

    op.create_index(
        op.f("ix_payment_intents_expires_at"),
        "payment_intents",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_payment_intents_expires_at"),
        table_name="payment_intents",
    )

    op.drop_column(
        "payment_intents",
        "expires_at",
    )
