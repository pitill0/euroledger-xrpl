from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.domain.exceptions import WebhookDeliveryRetryConflictError
from app.models.webhook import WebhookDelivery, WebhookDeliveryStatus
from app.services.webhook_deliveries import retry_webhook_delivery

NOW = datetime(
    2026,
    6,
    19,
    20,
    0,
    tzinfo=UTC,
)


def build_delivery(
    *,
    status: WebhookDeliveryStatus = WebhookDeliveryStatus.failed,
) -> WebhookDelivery:
    return WebhookDelivery(
        id="delivery-id",
        merchant_id="merchant-id",
        endpoint_id="endpoint-id",
        event_type="payment_intent.confirmed",
        payment_intent_id="intent-id",
        payload={
            "type": "payment_intent.confirmed",
            "data": {
                "object": {
                    "id": "intent-id",
                },
            },
        },
        status=status,
        attempt_count=3,
        next_attempt_at=NOW + timedelta(hours=1),
        last_attempt_at=NOW - timedelta(minutes=5),
        response_status_code=500,
        response_body="temporary failure",
        error_message="Webhook endpoint returned HTTP 500.",
        created_at=NOW - timedelta(minutes=10),
        updated_at=NOW,
    )


def test_retry_webhook_delivery_requeues_failed_delivery() -> None:
    db = Mock()
    delivery = build_delivery(status=WebhookDeliveryStatus.failed)

    result = retry_webhook_delivery(
        db=db,
        delivery=delivery,
        now=NOW,
    )

    assert result is delivery
    assert delivery.status == WebhookDeliveryStatus.pending
    assert delivery.attempt_count == 0
    assert delivery.next_attempt_at == NOW
    assert delivery.last_attempt_at is None
    assert delivery.response_status_code is None
    assert delivery.response_body is None
    assert delivery.error_message is None

    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(delivery)


def test_retry_webhook_delivery_requeues_discarded_delivery() -> None:
    db = Mock()
    delivery = build_delivery(status=WebhookDeliveryStatus.discarded)

    retry_webhook_delivery(
        db=db,
        delivery=delivery,
        now=NOW,
    )

    assert delivery.status == WebhookDeliveryStatus.pending
    assert delivery.attempt_count == 0
    assert delivery.next_attempt_at == NOW

    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(delivery)


def test_retry_webhook_delivery_requeues_pending_delivery() -> None:
    db = Mock()
    delivery = build_delivery(status=WebhookDeliveryStatus.pending)

    retry_webhook_delivery(
        db=db,
        delivery=delivery,
        now=NOW,
    )

    assert delivery.status == WebhookDeliveryStatus.pending
    assert delivery.attempt_count == 0
    assert delivery.next_attempt_at == NOW

    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(delivery)


def test_retry_webhook_delivery_rejects_delivered_delivery() -> None:
    db = Mock()
    delivery = build_delivery(status=WebhookDeliveryStatus.delivered)

    with pytest.raises(WebhookDeliveryRetryConflictError):
        retry_webhook_delivery(
            db=db,
            delivery=delivery,
            now=NOW,
        )

    db.commit.assert_not_called()
    db.refresh.assert_not_called()
