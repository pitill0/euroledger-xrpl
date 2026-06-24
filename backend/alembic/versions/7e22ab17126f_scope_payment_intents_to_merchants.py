"""scope payment intents to merchants

Revision ID: 7e22ab17126f
Revises: 237db2a44e88
Create Date: 2026-06-12 19:26:36.567587

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e22ab17126f"
down_revision: str | None = "237db2a44e88"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    legacy_merchant_id = "00000000-0000-0000-0000-000000000001"

    op.execute(
        sa.text(
            """
            INSERT INTO merchants (id, name, slug, is_active)
            VALUES (
                :merchant_id,
                'Legacy unscoped payment intents',
                'legacy-unscoped',
                true
            )
            ON CONFLICT (slug) DO NOTHING
            """
        ).bindparams(merchant_id=legacy_merchant_id)
    )

    op.add_column(
        "payment_intents",
        sa.Column(
            "merchant_id",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE payment_intents
            SET merchant_id = :merchant_id
            WHERE merchant_id IS NULL
            """
        ).bindparams(merchant_id=legacy_merchant_id)
    )

    op.alter_column(
        "payment_intents",
        "merchant_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )

    op.create_index(
        "ix_payment_intents_merchant_id",
        "payment_intents",
        ["merchant_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_payment_intents_merchant_id_merchants",
        "payment_intents",
        "merchants",
        ["merchant_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_index(
        "ix_payment_intents_idempotency_key",
        table_name="payment_intents",
    )

    op.create_unique_constraint(
        "uq_payment_intents_merchant_id_idempotency_key",
        "payment_intents",
        ["merchant_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_payment_intents_merchant_id_idempotency_key",
        "payment_intents",
        type_="unique",
    )

    op.create_index(
        "ix_payment_intents_idempotency_key",
        "payment_intents",
        ["idempotency_key"],
        unique=True,
    )

    op.drop_constraint(
        "fk_payment_intents_merchant_id_merchants",
        "payment_intents",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_payment_intents_merchant_id",
        table_name="payment_intents",
    )

    op.drop_column(
        "payment_intents",
        "merchant_id",
    )
