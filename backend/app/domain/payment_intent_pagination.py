import base64
import binascii
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.exceptions import (
    InvalidPaymentIntentCursorError,
)


@dataclass(frozen=True)
class PaymentIntentCursor:
    created_at: datetime
    payment_intent_id: str


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def encode_payment_intent_cursor(
    cursor: PaymentIntentCursor,
) -> str:
    payload = {
        "created_at": ensure_utc(
            cursor.created_at,
        ).isoformat(),
        "id": cursor.payment_intent_id,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return base64.urlsafe_b64encode(
        serialized,
    ).decode("ascii")


def decode_payment_intent_cursor(
    value: str,
) -> PaymentIntentCursor:
    try:
        decoded = base64.b64decode(
            value.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )

        payload = json.loads(
            decoded.decode("utf-8"),
        )

        created_at_raw = payload["created_at"]
        payment_intent_id = payload["id"]

        if not isinstance(created_at_raw, str):
            raise TypeError

        if not isinstance(payment_intent_id, str) or not payment_intent_id:
            raise TypeError

        created_at = datetime.fromisoformat(
            created_at_raw,
        )

        return PaymentIntentCursor(
            created_at=ensure_utc(created_at),
            payment_intent_id=payment_intent_id,
        )
    except (
        UnicodeEncodeError,
        UnicodeDecodeError,
        binascii.Error,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise InvalidPaymentIntentCursorError(
            "Invalid payment intent pagination cursor.",
        ) from exc
