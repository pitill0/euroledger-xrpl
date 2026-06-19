from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import URLError
from uuid import uuid4

from app.models.webhook import MerchantWebhookEndpoint
from app.services.webhook_delivery import (
    DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
    post_webhook,
    truncate_response_body,
)
from app.services.webhook_signing import build_webhook_headers, serialize_webhook_payload

WEBHOOK_ENDPOINT_TEST_EVENT = "webhook_endpoint.test"


@dataclass(frozen=True)
class WebhookEndpointTestResult:
    event_type: str
    delivery_id: str
    payload: dict[str, object]
    delivered: bool
    response_status_code: int | None
    response_body: str | None
    error_message: str | None


def utc_now() -> datetime:
    return datetime.now(UTC)


def build_webhook_endpoint_test_payload(
    *,
    endpoint: MerchantWebhookEndpoint,
    occurred_at: datetime,
) -> dict[str, object]:
    return {
        "type": WEBHOOK_ENDPOINT_TEST_EVENT,
        "created_at": occurred_at.isoformat(),
        "merchant_id": endpoint.merchant_id,
        "data": {
            "object": {
                "id": endpoint.id,
                "merchant_id": endpoint.merchant_id,
                "url": endpoint.url,
                "enabled": endpoint.enabled,
            },
        },
    }


def send_webhook_endpoint_test(
    endpoint: MerchantWebhookEndpoint,
    *,
    now: datetime | None = None,
    timeout: float = DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
) -> WebhookEndpointTestResult:
    occurred_at = now or utc_now()
    delivery_id = f"test-{uuid4()}"
    payload = build_webhook_endpoint_test_payload(
        endpoint=endpoint,
        occurred_at=occurred_at,
    )
    raw_body = serialize_webhook_payload(payload)
    timestamp = int(occurred_at.timestamp())
    headers = build_webhook_headers(
        event_type=WEBHOOK_ENDPOINT_TEST_EVENT,
        delivery_id=delivery_id,
        secret=endpoint.secret,
        timestamp=timestamp,
        raw_body=raw_body,
    )

    try:
        response = post_webhook(
            url=endpoint.url,
            raw_body=raw_body,
            headers=headers,
            timeout=timeout,
        )
    except (TimeoutError, URLError, OSError) as exc:
        return WebhookEndpointTestResult(
            event_type=WEBHOOK_ENDPOINT_TEST_EVENT,
            delivery_id=delivery_id,
            payload=payload,
            delivered=False,
            response_status_code=None,
            response_body=None,
            error_message=str(exc),
        )

    delivered = 200 <= response.status_code < 300
    error_message = None

    if not delivered:
        error_message = f"Webhook endpoint returned HTTP {response.status_code}."

    return WebhookEndpointTestResult(
        event_type=WEBHOOK_ENDPOINT_TEST_EVENT,
        delivery_id=delivery_id,
        payload=payload,
        delivered=delivered,
        response_status_code=response.status_code,
        response_body=truncate_response_body(response.body),
        error_message=error_message,
    )
