from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from app.models.webhook import (
    MerchantWebhookEndpoint,
    WebhookDelivery,
    WebhookDeliveryStatus,
)
from app.services.webhook_delivery import (
    WebhookHttpResponse,
    calculate_next_attempt_at,
    deliver_webhook,
    process_due_webhook_deliveries,
)

NOW = datetime(
    2026,
    6,
    19,
    16,
    0,
    tzinfo=UTC,
)


def build_endpoint(
    *,
    enabled: bool = True,
) -> MerchantWebhookEndpoint:
    return MerchantWebhookEndpoint(
        id="endpoint-id",
        merchant_id="merchant-id",
        url="https://merchant.example.com/webhooks/euroledger",
        secret="super-secret-value",
        enabled=enabled,
        created_at=NOW,
        updated_at=NOW,
    )


def build_delivery(
    *,
    endpoint: MerchantWebhookEndpoint | None = None,
    attempt_count: int = 0,
) -> WebhookDelivery:
    return WebhookDelivery(
        id="delivery-id",
        merchant_id="merchant-id",
        endpoint_id="endpoint-id" if endpoint is not None else None,
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
        status=WebhookDeliveryStatus.pending,
        attempt_count=attempt_count,
        next_attempt_at=NOW,
        endpoint=endpoint,
        created_at=NOW,
        updated_at=NOW,
    )


def test_calculate_next_attempt_at_uses_exponential_backoff() -> None:
    assert calculate_next_attempt_at(
        now=NOW,
        attempt_count=1,
    ) == NOW + timedelta(seconds=60)

    assert calculate_next_attempt_at(
        now=NOW,
        attempt_count=3,
    ) == NOW + timedelta(seconds=240)


def test_deliver_webhook_marks_delivered_on_2xx() -> None:
    endpoint = build_endpoint()
    delivery = build_delivery(endpoint=endpoint)

    with patch(
        "app.services.webhook_delivery.post_webhook",
        return_value=WebhookHttpResponse(
            status_code=204,
            body="",
        ),
    ) as post_webhook:
        result = deliver_webhook(
            delivery,
            now=NOW,
            timeout=5.0,
            max_attempts=5,
        )

    assert result == WebhookDeliveryStatus.delivered
    assert delivery.status == WebhookDeliveryStatus.delivered
    assert delivery.attempt_count == 1
    assert delivery.last_attempt_at == NOW
    assert delivery.next_attempt_at is None
    assert delivery.response_status_code == 204
    assert delivery.response_body == ""
    assert delivery.error_message is None

    call = post_webhook.call_args.kwargs

    assert call["url"] == "https://merchant.example.com/webhooks/euroledger"
    assert call["timeout"] == 5.0
    assert call["headers"]["X-EuroLedger-Event"] == "payment_intent.confirmed"
    assert call["headers"]["X-EuroLedger-Delivery"] == "delivery-id"
    assert call["headers"]["X-EuroLedger-Signature"].startswith("sha256=")


def test_deliver_webhook_retries_on_5xx() -> None:
    endpoint = build_endpoint()
    delivery = build_delivery(endpoint=endpoint)

    with patch(
        "app.services.webhook_delivery.post_webhook",
        return_value=WebhookHttpResponse(
            status_code=500,
            body="temporary failure",
        ),
    ):
        result = deliver_webhook(
            delivery,
            now=NOW,
            timeout=5.0,
            max_attempts=5,
        )

    assert result == WebhookDeliveryStatus.failed
    assert delivery.status == WebhookDeliveryStatus.failed
    assert delivery.attempt_count == 1
    assert delivery.next_attempt_at == NOW + timedelta(seconds=60)
    assert delivery.response_status_code == 500
    assert delivery.response_body == "temporary failure"
    assert delivery.error_message == "Webhook endpoint returned HTTP 500."


def test_deliver_webhook_discards_after_max_attempts() -> None:
    endpoint = build_endpoint()
    delivery = build_delivery(
        endpoint=endpoint,
        attempt_count=4,
    )

    with patch(
        "app.services.webhook_delivery.post_webhook",
        return_value=WebhookHttpResponse(
            status_code=500,
            body="temporary failure",
        ),
    ):
        result = deliver_webhook(
            delivery,
            now=NOW,
            timeout=5.0,
            max_attempts=5,
        )

    assert result == WebhookDeliveryStatus.discarded
    assert delivery.status == WebhookDeliveryStatus.discarded
    assert delivery.attempt_count == 5
    assert delivery.next_attempt_at is None
    assert delivery.error_message == "Webhook endpoint returned HTTP 500."


def test_deliver_webhook_discards_delivery_without_endpoint() -> None:
    delivery = build_delivery(endpoint=None)

    result = deliver_webhook(
        delivery,
        now=NOW,
        timeout=5.0,
        max_attempts=5,
    )

    assert result == WebhookDeliveryStatus.discarded
    assert delivery.status == WebhookDeliveryStatus.discarded
    assert delivery.error_message == "Webhook endpoint no longer exists."


def test_deliver_webhook_discards_delivery_for_disabled_endpoint() -> None:
    endpoint = build_endpoint(enabled=False)
    delivery = build_delivery(endpoint=endpoint)

    result = deliver_webhook(
        delivery,
        now=NOW,
        timeout=5.0,
        max_attempts=5,
    )

    assert result == WebhookDeliveryStatus.discarded
    assert delivery.status == WebhookDeliveryStatus.discarded
    assert delivery.error_message == "Webhook endpoint is disabled."


def test_process_due_webhook_deliveries_commits_batch_result() -> None:
    db = Mock()
    delivered_delivery = build_delivery(endpoint=build_endpoint())
    failed_delivery = build_delivery(endpoint=build_endpoint())

    with (
        patch(
            "app.services.webhook_delivery.list_due_webhook_deliveries",
            return_value=[
                delivered_delivery,
                failed_delivery,
            ],
        ) as list_deliveries,
        patch(
            "app.services.webhook_delivery.deliver_webhook",
            side_effect=[
                WebhookDeliveryStatus.delivered,
                WebhookDeliveryStatus.failed,
            ],
        ) as deliver,
    ):
        result = process_due_webhook_deliveries(
            db=db,
            limit=100,
            timeout=5.0,
            max_attempts=5,
            now=NOW,
        )

    list_deliveries.assert_called_once_with(
        db=db,
        now=NOW,
        limit=100,
    )
    assert deliver.call_count == 2
    db.commit.assert_called_once_with()

    assert result.processed == 2
    assert result.delivered == 1
    assert result.failed == 1
    assert result.discarded == 0
    assert result.limit == 100
