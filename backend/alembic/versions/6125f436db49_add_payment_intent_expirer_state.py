"""add payment intent expirer state

Revision ID: 6125f436db49
Revises: 541c7e6496cd
Create Date: 2026-06-11 17:02:07.504939

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6125f436db49'
down_revision: str | None = '541c7e6496cd'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_intent_expirer_states",
        sa.Column(
            "worker_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "last_cycle_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_success_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "successful_cycles_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "failed_cycles_total",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "expired_payment_intents_total",
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
    op.execute(
        "DROP TABLE IF EXISTS payment_intent_expirer_states"
    )
