import hashlib
import hmac
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue
from threading import Thread

from app.models.webhook import (
    MerchantWebhookEndpoint,
    WebhookDelivery,
    WebhookDeliveryStatus,
)
from app.services.webhook_delivery import deliver_webhook

NOW = datetime(
    2026,
    6,
    19,
    18,
    0,
    tzinfo=UTC,
)

WEBHOOK_SECRET = "super-secret-value"


def build_endpoint(
    *,
    url: str,
) -> MerchantWebhookEndpoint:
    return MerchantWebhookEndpoint(
        id="endpoint-id",
        merchant_id="merchant-id",
        url=url,
        secret=WEBHOOK_SECRET,
        enabled=True,
        created_at=NOW,
        updated_at=NOW,
    )


def build_delivery(
    *,
    endpoint: MerchantWebhookEndpoint,
) -> WebhookDelivery:
    return WebhookDelivery(
        id="delivery-id",
        merchant_id="merchant-id",
        endpoint_id=endpoint.id,
        event_type="payment_intent.confirmed",
        payment_intent_id="intent-id",
        payload={
            "type": "payment_intent.confirmed",
            "data": {
                "object": {
                    "id": "intent-id",
                    "reference": "EL-TESTREFERENCE",
                },
            },
        },
        status=WebhookDeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=NOW,
        endpoint=endpoint,
        created_at=NOW,
        updated_at=NOW,
    )


def expected_signature(
    *,
    timestamp: str,
    raw_body: bytes,
) -> str:
    digest = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        timestamp.encode("utf-8") + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def test_deliver_webhook_posts_signed_payload_to_real_http_receiver() -> None:
    received_requests: Queue[dict[str, object]] = Queue()

    class WebhookReceiver(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers["Content-Length"])
            raw_body = self.rfile.read(content_length)

            received_requests.put(
                {
                    "path": self.path,
                    "headers": dict(self.headers),
                    "raw_body": raw_body,
                }
            )

            self.send_response(204)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = HTTPServer(
        ("127.0.0.1", 0),
        WebhookReceiver,
    )
    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address
        endpoint = build_endpoint(
            url=f"http://{host}:{port}/euroledger-webhooks",
        )
        delivery = build_delivery(
            endpoint=endpoint,
        )

        result = deliver_webhook(
            delivery,
            now=NOW,
            timeout=5.0,
            max_attempts=5,
        )

        received_request = received_requests.get(timeout=5.0)
    finally:
        server.shutdown()
        server.server_close()

    assert result == WebhookDeliveryStatus.delivered
    assert delivery.status == WebhookDeliveryStatus.delivered
    assert delivery.attempt_count == 1
    assert delivery.last_attempt_at == NOW
    assert delivery.next_attempt_at is None
    assert delivery.response_status_code == 204
    assert delivery.response_body == ""
    assert delivery.error_message is None

    headers = received_request["headers"]
    raw_body = received_request["raw_body"]

    assert received_request["path"] == "/euroledger-webhooks"
    assert raw_body == (
        b'{"type":"payment_intent.confirmed",'
        b'"data":{"object":{"id":"intent-id","reference":"EL-TESTREFERENCE"}}}'
    )

    assert headers["X-Euroledger-Event"] == "payment_intent.confirmed"
    assert headers["X-Euroledger-Delivery"] == "delivery-id"
    assert headers["X-Euroledger-Timestamp"] == str(int(NOW.timestamp()))
    assert headers["X-Euroledger-Signature"] == expected_signature(
        timestamp=headers["X-Euroledger-Timestamp"],
        raw_body=raw_body,
    )
