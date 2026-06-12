from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from app.models.payment_intent import (
    PaymentIntentStatus,
)
from app.services.payment_intent_state_metrics import (
    generate_payment_intent_state_metrics,
)

NOW = datetime(
    2026,
    6,
    12,
    15,
    0,
    tzinfo=UTC,
)


def test_generate_payment_intent_state_metrics() -> None:
    db = Mock()

    status_counts = {
        PaymentIntentStatus.pending: 5,
        PaymentIntentStatus.confirmed: 7,
        PaymentIntentStatus.expired: 3,
        PaymentIntentStatus.cancelled: 2,
    }

    oldest_pending = NOW - timedelta(
        seconds=600,
    )

    with (
        patch(
            ("app.services.payment_intent_state_metrics.get_payment_intent_status_counts"),
            return_value=status_counts,
        ),
        patch(
            ("app.services.payment_intent_state_metrics.get_oldest_pending_created_at"),
            return_value=oldest_pending,
        ),
        patch(
            ("app.services.payment_intent_state_metrics.get_past_due_pending_count"),
            return_value=2,
        ),
    ):
        result = generate_payment_intent_state_metrics(
            db=db,
            now=NOW,
        )

    metrics = result.decode()

    assert 'euroledger_payment_intents_by_status{status="pending"} 5.0' in metrics

    assert 'euroledger_payment_intents_by_status{status="confirmed"} 7.0' in metrics

    assert 'euroledger_payment_intents_by_status{status="expired"} 3.0' in metrics

    assert 'euroledger_payment_intents_by_status{status="cancelled"} 2.0' in metrics

    assert "euroledger_payment_intent_oldest_pending_age_seconds 600.0" in metrics

    assert "euroledger_payment_intents_pending_past_due 2.0" in metrics


def test_state_metrics_without_pending_intents() -> None:
    db = Mock()

    status_counts = {status: 0 for status in PaymentIntentStatus}

    with (
        patch(
            ("app.services.payment_intent_state_metrics.get_payment_intent_status_counts"),
            return_value=status_counts,
        ),
        patch(
            ("app.services.payment_intent_state_metrics.get_oldest_pending_created_at"),
            return_value=None,
        ),
        patch(
            ("app.services.payment_intent_state_metrics.get_past_due_pending_count"),
            return_value=0,
        ),
    ):
        result = generate_payment_intent_state_metrics(
            db=db,
            now=NOW,
        )

    metrics = result.decode()

    assert "euroledger_payment_intent_oldest_pending_age_seconds 0.0" in metrics

    assert "euroledger_payment_intents_pending_past_due 0.0" in metrics
