from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from app.domain.exceptions import (
    InvalidPaymentIntentStatusTransitionError,
    PaymentIntentCancellationConflictError,
)
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.services.payment_intents import (
    cancel_payment_intent,
)
from app.services.webhook_events import PAYMENT_INTENT_CANCELLED_EVENT

NOW = datetime(
    2026,
    6,
    12,
    16,
    0,
    tzinfo=UTC,
)


def build_payment_intent(
    *,
    status: PaymentIntentStatus = PaymentIntentStatus.pending,
    cancellation_reason: str | None = None,
    cancelled_at: datetime | None = None,
) -> PaymentIntent:
    return PaymentIntent(
        id="intent-id",
        merchant_id="merchant-id",
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=status,
        cancellation_reason=cancellation_reason,
        cancelled_at=cancelled_at,
    )


def test_cancel_pending_payment_intent() -> None:
    db = Mock()
    payment_intent = build_payment_intent()

    with patch(
        "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
    ) as enqueue_deliveries:
        result = cancel_payment_intent(
            db=db,
            payment_intent=payment_intent,
            reason="Customer request",
            now=NOW,
        )

    assert result.cancelled is True
    assert result.payment_intent is payment_intent
    assert payment_intent.status == PaymentIntentStatus.cancelled
    assert payment_intent.cancelled_at == NOW
    assert payment_intent.cancellation_reason == "Customer request"

    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(payment_intent)

    enqueue_deliveries.assert_called_once_with(
        db=db,
        payment_intent=payment_intent,
        event_type=PAYMENT_INTENT_CANCELLED_EVENT,
        occurred_at=NOW,
    )


def test_cancel_pending_payment_intent_without_reason() -> None:
    db = Mock()
    payment_intent = build_payment_intent()

    with patch(
        "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
    ):
        result = cancel_payment_intent(
            db=db,
            payment_intent=payment_intent,
            reason=None,
            now=NOW,
        )

    assert result.cancelled is True
    assert payment_intent.cancellation_reason is None
    assert payment_intent.cancelled_at == NOW


def test_repeating_same_cancellation_is_idempotent() -> None:
    db = Mock()

    payment_intent = build_payment_intent(
        status=PaymentIntentStatus.cancelled,
        cancellation_reason="Customer request",
        cancelled_at=NOW,
    )

    with patch(
        "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
    ) as enqueue_deliveries:
        result = cancel_payment_intent(
            db=db,
            payment_intent=payment_intent,
            reason="Customer request",
            now=NOW,
        )

    assert result.cancelled is False
    assert result.payment_intent is payment_intent

    db.commit.assert_not_called()
    db.refresh.assert_not_called()
    enqueue_deliveries.assert_not_called()


def test_repeating_cancellation_with_different_reason_fails() -> None:
    db = Mock()

    payment_intent = build_payment_intent(
        status=PaymentIntentStatus.cancelled,
        cancellation_reason="Customer request",
        cancelled_at=NOW,
    )

    with patch(
        "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
    ) as enqueue_deliveries:
        with pytest.raises(
            PaymentIntentCancellationConflictError,
            match="different reason",
        ):
            cancel_payment_intent(
                db=db,
                payment_intent=payment_intent,
                reason="Duplicate order",
                now=NOW,
            )

    db.commit.assert_not_called()
    db.refresh.assert_not_called()
    enqueue_deliveries.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        PaymentIntentStatus.confirmed,
        PaymentIntentStatus.expired,
    ],
)
def test_cannot_cancel_terminal_payment_intent(
    status: PaymentIntentStatus,
) -> None:
    db = Mock()
    payment_intent = build_payment_intent(
        status=status,
    )

    with patch(
        "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
    ) as enqueue_deliveries:
        with pytest.raises(
            InvalidPaymentIntentStatusTransitionError,
            match="Cannot cancel",
        ):
            cancel_payment_intent(
                db=db,
                payment_intent=payment_intent,
                reason="Customer request",
                now=NOW,
            )

    db.commit.assert_not_called()
    db.refresh.assert_not_called()
    enqueue_deliveries.assert_not_called()
