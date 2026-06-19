import hashlib
import hmac

from app.services.webhook_signing import (
    build_webhook_headers,
    serialize_webhook_payload,
    sign_webhook_payload,
)


def test_serialize_webhook_payload_uses_compact_json() -> None:
    raw_body = serialize_webhook_payload(
        {
            "type": "payment_intent.confirmed",
            "data": {
                "object": {
                    "id": "intent-id",
                },
            },
        }
    )

    assert raw_body == (
        b'{"type":"payment_intent.confirmed","data":{"object":{"id":"intent-id"}}}'
    )


def test_sign_webhook_payload_uses_timestamp_and_raw_body() -> None:
    raw_body = b'{"type":"payment_intent.confirmed"}'
    timestamp = 1781874000
    secret = "super-secret-value"

    expected_digest = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + raw_body,
        hashlib.sha256,
    ).hexdigest()

    signature = sign_webhook_payload(
        secret=secret,
        timestamp=timestamp,
        raw_body=raw_body,
    )

    assert signature == f"sha256={expected_digest}"


def test_build_webhook_headers() -> None:
    raw_body = b'{"type":"payment_intent.confirmed"}'

    headers = build_webhook_headers(
        event_type="payment_intent.confirmed",
        delivery_id="delivery-id",
        secret="super-secret-value",
        timestamp=1781874000,
        raw_body=raw_body,
    )

    assert headers["Content-Type"] == "application/json"
    assert headers["X-EuroLedger-Event"] == "payment_intent.confirmed"
    assert headers["X-EuroLedger-Delivery"] == "delivery-id"
    assert headers["X-EuroLedger-Timestamp"] == "1781874000"
    assert headers["X-EuroLedger-Signature"].startswith("sha256=")
