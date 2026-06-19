from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.payment_intents import (
    create_payment_intent,
    expire_pending_payment_intents,
)
from app.services.webhook_events import PAYMENT_INTENT_EXPIRED_EVENT

NOW = datetime(
    2026,
    6,
    11,
    10,
    0,
    tzinfo=UTC,
)


def build_payment_intent(
    *,
    status: PaymentIntentStatus = PaymentIntentStatus.pending,
    expires_at: datetime | None = None,
) -> PaymentIntent:
    return PaymentIntent(
        merchant_id="merchant-id",
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=status,
        expires_at=expires_at or NOW,
    )


def test_create_payment_intent_sets_default_expiration() -> None:
    db = Mock()

    payload = PaymentIntentCreate(
        amount="25.00",
    )

    with patch(
        "app.services.payment_intents.generate_payment_reference",
        return_value="EL-TESTREFERENCE",
    ):
        result = create_payment_intent(
            db=db,
            payload=payload,
            merchant_id="merchant-id",
            now=NOW,
        )

    payment_intent = result.payment_intent

    assert result.created is True
    assert payment_intent.expires_at == NOW + timedelta(
        seconds=900,
    )
    assert payment_intent.idempotency_key is None
    assert payment_intent.idempotency_fingerprint is None

    db.add.assert_called_once_with(payment_intent)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(payment_intent)


def test_create_payment_intent_accepts_custom_expiration() -> None:
    db = Mock()

    payload = PaymentIntentCreate(
        amount="25.00",
        expires_in_seconds=1800,
    )

    with patch(
        "app.services.payment_intents.generate_payment_reference",
        return_value="EL-TESTREFERENCE",
    ):
        result = create_payment_intent(
            db=db,
            payload=payload,
            merchant_id="merchant-id",
            now=NOW,
        )

    payment_intent = result.payment_intent

    assert result.created is True
    assert payment_intent.expires_at == NOW + timedelta(
        seconds=1800,
    )
    assert payment_intent.idempotency_key is None
    assert payment_intent.idempotency_fingerprint is None


def test_expire_pending_payment_intents() -> None:
    db = Mock()

    first = build_payment_intent()
    second = build_payment_intent()

    with (
        patch(
            ("app.services.payment_intents.get_expired_pending_payment_intents"),
            return_value=[first, second],
        ) as get_expired,
        patch(
            "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
        ) as enqueue_deliveries,
    ):
        result = expire_pending_payment_intents(
            db=db,
            limit=100,
            now=NOW,
        )

    get_expired.assert_called_once_with(
        db=db,
        expires_before=NOW,
        limit=100,
    )

    assert first.status == PaymentIntentStatus.expired
    assert second.status == PaymentIntentStatus.expired
    assert result.expired == 2
    assert result.limit == 100

    db.commit.assert_called_once_with()

    assert enqueue_deliveries.call_count == 2
    enqueue_deliveries.assert_any_call(
        db=db,
        payment_intent=first,
        event_type=PAYMENT_INTENT_EXPIRED_EVENT,
        occurred_at=NOW,
    )
    enqueue_deliveries.assert_any_call(
        db=db,
        payment_intent=second,
        event_type=PAYMENT_INTENT_EXPIRED_EVENT,
        occurred_at=NOW,
    )


def test_expiration_cycle_with_no_matches() -> None:
    db = Mock()

    with (
        patch(
            ("app.services.payment_intents.get_expired_pending_payment_intents"),
            return_value=[],
        ),
        patch(
            "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
        ) as enqueue_deliveries,
    ):
        result = expire_pending_payment_intents(
            db=db,
            limit=100,
            now=NOW,
        )

    assert result.expired == 0
    assert result.limit == 100

    db.commit.assert_called_once_with()
    enqueue_deliveries.assert_not_called()
