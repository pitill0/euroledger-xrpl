from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.payment_intent import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant
    from app.models.payment_intent import PaymentIntent


class WebhookDeliveryStatus(StrEnum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"
    discarded = "discarded"


class MerchantWebhookEndpoint(Base):
    __tablename__ = "merchant_webhook_endpoints"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    merchant_id: Mapped[str] = mapped_column(
        ForeignKey(
            "merchants.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    secret: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
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

    merchant: Mapped["Merchant"] = relationship(
        back_populates="webhook_endpoints",
    )

    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        back_populates="endpoint",
    )


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    merchant_id: Mapped[str] = mapped_column(
        ForeignKey(
            "merchants.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    endpoint_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "merchant_webhook_endpoints.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    payment_intent_id: Mapped[str] = mapped_column(
        ForeignKey(
            "payment_intents.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        String(20),
        default=WebhookDeliveryStatus.pending,
        nullable=False,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    response_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    response_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
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

    merchant: Mapped["Merchant"] = relationship()

    endpoint: Mapped[MerchantWebhookEndpoint | None] = relationship(
        back_populates="deliveries",
    )

    payment_intent: Mapped["PaymentIntent"] = relationship()
