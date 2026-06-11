"""add worker health fields

Revision ID: 75a36d9956f0
Revises: 29cc43e7b7c1
Create Date: 2026-06-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "75a36d9956f0"
down_revision: str | None = "29cc43e7b7c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "worker_states",
        sa.Column(
            "last_cycle_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "last_success_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "last_error_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "worker_states",
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("worker_states", "last_error")
    op.drop_column("worker_states", "last_error_at")
    op.drop_column("worker_states", "last_success_at")
    op.drop_column("worker_states", "last_cycle_started_at")
