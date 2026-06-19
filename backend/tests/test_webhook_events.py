from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.models.webhook import MerchantWebhookEndpoint, WebhookDeliveryStatus
from app.services.webhook_events import (
    PAYMENT_INTENT_CONFIRMED_EVENT,
    build_payment_intent_webhook_payload,
    enqueue_payment_intent_webhook_deliveries,
)

NOW = datetime(
    2026,
    6,
    19,
    15,
    0,
    tzinfo=UTC,
)


def build_payment_intent() -> PaymentIntent:
    return PaymentIntent(
        id="intent-id",
        merchant_id="merchant-id",
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=PaymentIntentStatus.confirmed,
        description="Order 123",
        expected_destination="rDestination",
        xrpl_transaction_hash="A" * 64,
        expires_at=NOW + timedelta(minutes=15),
        cancelled_at=None,
        cancellation_reason=None,
        created_at=NOW - timedelta(minutes=5),
        updated_at=NOW,
    )


def build_endpoint(
    endpoint_id: str,
) -> MerchantWebhookEndpoint:
    return MerchantWebhookEndpoint(
        id=endpoint_id,
        merchant_id="merchant-id",
        url=f"https://merchant.example.com/{endpoint_id}",
        secret="super-secret-value",
        enabled=True,
        created_at=NOW,
        updated_at=NOW,
    )


def test_build_payment_intent_webhook_payload() -> None:
    payment_intent = build_payment_intent()

    payload = build_payment_intent_webhook_payload(
        event_type=PAYMENT_INTENT_CONFIRMED_EVENT,
        payment_intent=payment_intent,
        occurred_at=NOW,
    )

    assert payload["type"] == PAYMENT_INTENT_CONFIRMED_EVENT
    assert payload["created_at"] == NOW.isoformat()
    assert payload["merchant_id"] == "merchant-id"

    payment_intent_payload = payload["data"]["object"]

    assert payment_intent_payload["id"] == "intent-id"
    assert payment_intent_payload["merchant_id"] == "merchant-id"
    assert payment_intent_payload["reference"] == "EL-TESTREFERENCE"
    assert payment_intent_payload["amount"] == "25.00"
    assert payment_intent_payload["currency"] == "EUR"
    assert payment_intent_payload["status"] == PaymentIntentStatus.confirmed
    assert payment_intent_payload["xrpl_transaction_hash"] == "A" * 64


def test_enqueue_payment_intent_webhook_deliveries_skips_merchants_without_endpoints() -> None:
    db = Mock()
    payment_intent = build_payment_intent()

    with (
        patch(
            "app.services.webhook_events.list_enabled_webhook_endpoints",
            return_value=[],
        ) as list_endpoints,
        patch(
            "app.services.webhook_events.add_webhook_delivery",
        ) as add_delivery,
    ):
        deliveries = enqueue_payment_intent_webhook_deliveries(
            db=db,
            payment_intent=payment_intent,
            event_type=PAYMENT_INTENT_CONFIRMED_EVENT,
            occurred_at=NOW,
        )

    assert deliveries == []

    list_endpoints.assert_called_once_with(
        db=db,
        merchant_id="merchant-id",
    )
    add_delivery.assert_not_called()


def test_enqueue_payment_intent_webhook_deliveries_creates_pending_delivery_per_endpoint() -> None:
    db = Mock()
    payment_intent = build_payment_intent()
    first_endpoint = build_endpoint("endpoint-a")
    second_endpoint = build_endpoint("endpoint-b")

    with patch(
        "app.services.webhook_events.list_enabled_webhook_endpoints",
        return_value=[
            first_endpoint,
            second_endpoint,
        ],
    ):
        deliveries = enqueue_payment_intent_webhook_deliveries(
            db=db,
            payment_intent=payment_intent,
            event_type=PAYMENT_INTENT_CONFIRMED_EVENT,
            occurred_at=NOW,
        )

    assert len(deliveries) == 2

    assert deliveries[0].merchant_id == "merchant-id"
    assert deliveries[0].endpoint_id == "endpoint-a"
    assert deliveries[0].event_type == PAYMENT_INTENT_CONFIRMED_EVENT
    assert deliveries[0].payment_intent_id == "intent-id"
    assert deliveries[0].status == WebhookDeliveryStatus.pending
    assert deliveries[0].attempt_count == 0
    assert deliveries[0].next_attempt_at == NOW
    assert deliveries[0].payload["type"] == PAYMENT_INTENT_CONFIRMED_EVENT

    assert deliveries[1].endpoint_id == "endpoint-b"

    db.add.assert_any_call(deliveries[0])
    db.add.assert_any_call(deliveries[1])
    db.commit.assert_not_called()
