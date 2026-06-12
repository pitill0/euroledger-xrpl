from datetime import UTC, datetime

import pytest

from app.domain.exceptions import (
    InvalidPaymentIntentCursorError,
)
from app.domain.payment_intent_pagination import (
    PaymentIntentCursor,
    decode_payment_intent_cursor,
    encode_payment_intent_cursor,
)

CREATED_AT = datetime(
    2026,
    6,
    12,
    16,
    30,
    tzinfo=UTC,
)


def test_cursor_round_trip() -> None:
    original = PaymentIntentCursor(
        created_at=CREATED_AT,
        payment_intent_id="intent-id",
    )

    encoded = encode_payment_intent_cursor(
        original,
    )

    decoded = decode_payment_intent_cursor(
        encoded,
    )

    assert decoded == original


@pytest.mark.parametrize(
    "value",
    [
        "not-base64",
        "",
        "e30=",
    ],
)
def test_invalid_cursor_fails(
    value: str,
) -> None:
    with pytest.raises(
        InvalidPaymentIntentCursorError,
        match="Invalid payment intent pagination cursor",
    ):
        decode_payment_intent_cursor(value)
