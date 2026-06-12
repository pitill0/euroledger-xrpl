from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PaymentIntentStatus(StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    expired = "expired"
    cancelled = "cancelled"


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    reference: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        default="EUR",
    )

    status: Mapped[PaymentIntentStatus] = mapped_column(
        Enum(
            PaymentIntentStatus,
            name="payment_intent_status",
        ),
        nullable=False,
        default=PaymentIntentStatus.pending,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    expected_destination: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    xrpl_transaction_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    idempotency_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
