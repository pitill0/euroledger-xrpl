from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.idempotency import (
    IdempotencyConflictError,
    build_payment_intent_fingerprint,
)
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.payment_intents import (
    create_payment_intent,
)

NOW = datetime(
    2026,
    6,
    12,
    10,
    0,
    tzinfo=UTC,
)


def build_payload(
    *,
    amount: str = "25.00",
    description: str | None = "Order 123",
) -> PaymentIntentCreate:
    return PaymentIntentCreate(
        amount=amount,
        currency="eur",
        description=description,
        expected_destination="rMerchant",
        expires_in_seconds=900,
    )


def build_existing_payment_intent(
    payload: PaymentIntentCreate,
) -> PaymentIntent:
    return PaymentIntent(
        id="intent-id",
        merchant_id="merchant-id",
        reference="EL-TESTREFERENCE",
        amount=payload.amount,
        currency="EUR",
        description=payload.description,
        expected_destination=payload.expected_destination,
        expires_at=NOW,
        idempotency_key="order-123",
        idempotency_fingerprint=(build_payment_intent_fingerprint(payload)),
    )


def test_fingerprint_normalizes_currency_and_amount() -> None:
    first = PaymentIntentCreate(
        amount="25",
        currency="eur",
        expires_in_seconds=900,
    )

    second = PaymentIntentCreate(
        amount="25.00",
        currency="EUR",
        expires_in_seconds=900,
    )

    assert build_payment_intent_fingerprint(first) == build_payment_intent_fingerprint(second)


def test_create_without_idempotency_key_creates_new_intent() -> None:
    db = Mock()
    payload = build_payload()

    with (
        patch(
            "app.services.payment_intents.generate_payment_reference",
            return_value="EL-TESTREFERENCE",
        ),
        patch(
            "app.services.payment_intents.save_payment_intent",
            side_effect=lambda db, payment_intent: payment_intent,
        ) as save_payment_intent,
    ):
        result = create_payment_intent(
            db=db,
            payload=payload,
            merchant_id="merchant-id",
            now=NOW,
        )

    assert result.created is True
    assert result.payment_intent.idempotency_key is None
    assert result.payment_intent.idempotency_fingerprint is None

    save_payment_intent.assert_called_once()


def test_first_idempotent_request_creates_intent() -> None:
    db = Mock()
    payload = build_payload()

    with (
        patch(
            ("app.services.payment_intents.get_payment_intent_by_idempotency_key"),
            return_value=None,
        ),
        patch(
            "app.services.payment_intents.generate_payment_reference",
            return_value="EL-TESTREFERENCE",
        ),
        patch(
            "app.services.payment_intents.save_payment_intent",
            side_effect=lambda db, payment_intent: payment_intent,
        ),
    ):
        result = create_payment_intent(
            db=db,
            payload=payload,
            merchant_id="merchant-id",
            idempotency_key="order-123",
            now=NOW,
        )

    assert result.created is True
    assert result.payment_intent.idempotency_key == "order-123"
    assert result.payment_intent.idempotency_fingerprint == build_payment_intent_fingerprint(
        payload
    )


def test_idempotent_replay_returns_existing_intent() -> None:
    db = Mock()
    payload = build_payload()
    existing = build_existing_payment_intent(payload)

    with (
        patch(
            ("app.services.payment_intents.get_payment_intent_by_idempotency_key"),
            return_value=existing,
        ),
        patch(
            "app.services.payment_intents.save_payment_intent",
        ) as save_payment_intent,
    ):
        result = create_payment_intent(
            db=db,
            payload=payload,
            merchant_id="merchant-id",
            idempotency_key="order-123",
            now=NOW,
        )

    assert result.created is False
    assert result.payment_intent is existing
    save_payment_intent.assert_not_called()


def test_reusing_key_with_different_payload_fails() -> None:
    db = Mock()

    original_payload = build_payload()
    different_payload = build_payload(
        amount="30.00",
    )

    existing = build_existing_payment_intent(
        original_payload,
    )

    with patch(
        ("app.services.payment_intents.get_payment_intent_by_idempotency_key"),
        return_value=existing,
    ):
        with pytest.raises(
            IdempotencyConflictError,
            match="different payload",
        ):
            create_payment_intent(
                db=db,
                merchant_id="merchant-id",
                payload=different_payload,
                idempotency_key="order-123",
                now=NOW,
            )


def test_concurrent_duplicate_returns_persisted_intent() -> None:
    db = Mock()
    payload = build_payload()
    existing = build_existing_payment_intent(payload)

    integrity_error = IntegrityError(
        statement="INSERT",
        params={},
        orig=RuntimeError("duplicate key"),
    )

    with (
        patch(
            ("app.services.payment_intents.get_payment_intent_by_idempotency_key"),
            side_effect=[
                None,
                existing,
            ],
        ),
        patch(
            "app.services.payment_intents.generate_payment_reference",
            return_value="EL-NEWREFERENCE",
        ),
        patch(
            "app.services.payment_intents.save_payment_intent",
            side_effect=integrity_error,
        ),
    ):
        result = create_payment_intent(
            db=db,
            payload=payload,
            merchant_id="merchant-id",
            idempotency_key="order-123",
            now=NOW,
        )

    db.rollback.assert_called_once_with()
    assert result.created is False
    assert result.payment_intent is existing
