from datetime import UTC, datetime
from unittest.mock import patch
from urllib.error import URLError

from app.models.webhook import MerchantWebhookEndpoint
from app.services.webhook_delivery import WebhookHttpResponse
from app.services.webhook_endpoint_tests import (
    WEBHOOK_ENDPOINT_TEST_EVENT,
    build_webhook_endpoint_test_payload,
    send_webhook_endpoint_test,
)

NOW = datetime(
    2026,
    6,
    19,
    21,
    0,
    tzinfo=UTC,
)


def build_endpoint() -> MerchantWebhookEndpoint:
    return MerchantWebhookEndpoint(
        id="endpoint-id",
        merchant_id="merchant-id",
        url="https://merchant.example.com/webhooks/euroledger",
        secret="super-secret-value",
        enabled=True,
        created_at=NOW,
        updated_at=NOW,
    )


def test_build_webhook_endpoint_test_payload() -> None:
    endpoint = build_endpoint()

    payload = build_webhook_endpoint_test_payload(
        endpoint=endpoint,
        occurred_at=NOW,
    )

    assert payload == {
        "type": WEBHOOK_ENDPOINT_TEST_EVENT,
        "created_at": "2026-06-19T21:00:00+00:00",
        "merchant_id": "merchant-id",
        "data": {
            "object": {
                "id": "endpoint-id",
                "merchant_id": "merchant-id",
                "url": "https://merchant.example.com/webhooks/euroledger",
                "enabled": True,
            },
        },
    }


def test_send_webhook_endpoint_test_marks_delivered_on_2xx() -> None:
    endpoint = build_endpoint()

    with patch(
        "app.services.webhook_endpoint_tests.post_webhook",
        return_value=WebhookHttpResponse(
            status_code=204,
            body="",
        ),
    ) as post_webhook:
        result = send_webhook_endpoint_test(
            endpoint,
            now=NOW,
            timeout=5.0,
        )

    assert result.event_type == WEBHOOK_ENDPOINT_TEST_EVENT
    assert result.delivery_id.startswith("test-")
    assert result.delivered is True
    assert result.response_status_code == 204
    assert result.response_body == ""
    assert result.error_message is None

    call = post_webhook.call_args.kwargs

    assert call["url"] == "https://merchant.example.com/webhooks/euroledger"
    assert call["timeout"] == 5.0
    assert call["headers"]["X-EuroLedger-Event"] == WEBHOOK_ENDPOINT_TEST_EVENT
    assert call["headers"]["X-EuroLedger-Delivery"].startswith("test-")
    assert call["headers"]["X-EuroLedger-Signature"].startswith("sha256=")


def test_send_webhook_endpoint_test_reports_non_2xx_response() -> None:
    endpoint = build_endpoint()

    with patch(
        "app.services.webhook_endpoint_tests.post_webhook",
        return_value=WebhookHttpResponse(
            status_code=500,
            body="temporary failure",
        ),
    ):
        result = send_webhook_endpoint_test(
            endpoint,
            now=NOW,
        )

    assert result.delivered is False
    assert result.response_status_code == 500
    assert result.response_body == "temporary failure"
    assert result.error_message == "Webhook endpoint returned HTTP 500."


def test_send_webhook_endpoint_test_reports_transport_error() -> None:
    endpoint = build_endpoint()

    with patch(
        "app.services.webhook_endpoint_tests.post_webhook",
        side_effect=URLError("Connection refused"),
    ):
        result = send_webhook_endpoint_test(
            endpoint,
            now=NOW,
        )

    assert result.delivered is False
    assert result.response_status_code is None
    assert result.response_body is None
    assert "Connection refused" in (result.error_message or "")
