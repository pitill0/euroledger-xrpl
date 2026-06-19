from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.payment_intent import PaymentIntent
from app.models.webhook import WebhookDelivery, WebhookDeliveryStatus
from app.repositories.webhook_deliveries import add_webhook_delivery
from app.repositories.webhook_endpoints import list_enabled_webhook_endpoints

PAYMENT_INTENT_CONFIRMED_EVENT = "payment_intent.confirmed"
PAYMENT_INTENT_EXPIRED_EVENT = "payment_intent.expired"
PAYMENT_INTENT_CANCELLED_EVENT = "payment_intent.cancelled"


def utc_now() -> datetime:
    return datetime.now(UTC)


def serialize_decimal(value: Decimal | str) -> str:
    return format(Decimal(str(value)), "f")


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def build_payment_intent_webhook_payload(
    *,
    event_type: str,
    payment_intent: PaymentIntent,
    occurred_at: datetime,
) -> dict[str, Any]:
    return {
        "type": event_type,
        "created_at": occurred_at.isoformat(),
        "merchant_id": payment_intent.merchant_id,
        "data": {
            "object": {
                "id": payment_intent.id,
                "merchant_id": payment_intent.merchant_id,
                "reference": payment_intent.reference,
                "amount": serialize_decimal(payment_intent.amount),
                "currency": payment_intent.currency,
                "status": payment_intent.status,
                "description": payment_intent.description,
                "expected_destination": payment_intent.expected_destination,
                "xrpl_transaction_hash": payment_intent.xrpl_transaction_hash,
                "expires_at": serialize_datetime(payment_intent.expires_at),
                "cancelled_at": serialize_datetime(payment_intent.cancelled_at),
                "cancellation_reason": payment_intent.cancellation_reason,
                "created_at": serialize_datetime(payment_intent.created_at),
                "updated_at": serialize_datetime(payment_intent.updated_at),
            },
        },
    }


def enqueue_payment_intent_webhook_deliveries(
    db: Session,
    *,
    payment_intent: PaymentIntent,
    event_type: str,
    occurred_at: datetime | None = None,
) -> list[WebhookDelivery]:
    event_created_at = occurred_at or utc_now()
    endpoints = list_enabled_webhook_endpoints(
        db=db,
        merchant_id=payment_intent.merchant_id,
    )

    if not endpoints:
        return []

    payload = build_payment_intent_webhook_payload(
        event_type=event_type,
        payment_intent=payment_intent,
        occurred_at=event_created_at,
    )

    deliveries = [
        WebhookDelivery(
            merchant_id=payment_intent.merchant_id,
            endpoint_id=endpoint.id,
            event_type=event_type,
            payment_intent_id=payment_intent.id,
            payload=payload,
            status=WebhookDeliveryStatus.pending,
            attempt_count=0,
            next_attempt_at=event_created_at,
        )
        for endpoint in endpoints
    ]

    for delivery in deliveries:
        add_webhook_delivery(
            db,
            delivery,
        )

    return deliveries
