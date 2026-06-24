"""add merchant webhook tables

Revision ID: 9f1b2d3c4a5e
Revises: 7e22ab17126f
Create Date: 2026-06-19 13:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f1b2d3c4a5e"
down_revision: str | None = "7e22ab17126f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "merchant_webhook_endpoints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("merchant_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("secret", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_merchant_webhook_endpoints_merchant_id",
        "merchant_webhook_endpoints",
        ["merchant_id"],
        unique=False,
    )

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("merchant_id", sa.String(length=36), nullable=False),
        sa.Column("endpoint_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payment_intent_id", sa.String(length=36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["endpoint_id"],
            ["merchant_webhook_endpoints.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["payment_intent_id"],
            ["payment_intents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_deliveries_merchant_id",
        "webhook_deliveries",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_deliveries_endpoint_id",
        "webhook_deliveries",
        ["endpoint_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_deliveries_payment_intent_id",
        "webhook_deliveries",
        ["payment_intent_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_deliveries_status_next_attempt_at",
        "webhook_deliveries",
        ["status", "next_attempt_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_webhook_deliveries_status_next_attempt_at",
        table_name="webhook_deliveries",
    )
    op.drop_index("ix_webhook_deliveries_payment_intent_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_endpoint_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_merchant_id", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")

    op.drop_index(
        "ix_merchant_webhook_endpoints_merchant_id",
        table_name="merchant_webhook_endpoints",
    )
    op.drop_table("merchant_webhook_endpoints")
