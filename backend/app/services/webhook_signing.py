import hashlib
import hmac
import json
from typing import Any


def serialize_webhook_payload(
    payload: dict[str, Any],
) -> bytes:
    return json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")


def sign_webhook_payload(
    *,
    secret: str,
    timestamp: int,
    raw_body: bytes,
) -> str:
    signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
    digest = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def build_webhook_headers(
    *,
    event_type: str,
    delivery_id: str,
    secret: str,
    timestamp: int,
    raw_body: bytes,
) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-EuroLedger-Event": event_type,
        "X-EuroLedger-Delivery": delivery_id,
        "X-EuroLedger-Timestamp": str(timestamp),
        "X-EuroLedger-Signature": sign_webhook_payload(
            secret=secret,
            timestamp=timestamp,
            raw_body=raw_body,
        ),
    }
