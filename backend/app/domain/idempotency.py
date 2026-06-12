import hashlib
import json
from decimal import Decimal

from app.schemas.payment_intent import PaymentIntentCreate


class IdempotencyConflictError(Exception):
    pass


def normalize_amount(value: Decimal) -> str:
    return format(
        Decimal(value).quantize(Decimal("0.01")),
        "f",
    )


def build_payment_intent_fingerprint(
    payload: PaymentIntentCreate,
) -> str:
    canonical_payload = {
        "amount": normalize_amount(payload.amount),
        "currency": payload.currency.upper(),
        "description": payload.description,
        "expected_destination": payload.expected_destination,
        "expires_in_seconds": payload.expires_in_seconds,
    }

    serialized_payload = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )

    return hashlib.sha256(
        serialized_payload.encode("utf-8"),
    ).hexdigest()
