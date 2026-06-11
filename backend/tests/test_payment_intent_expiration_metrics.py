from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from app.models.payment_intent_expirer_state import (
    PaymentIntentExpirerState,
)
from app.schemas.worker_status import WorkerHealthStatus
from app.services.payment_intent_expiration_metrics import (
    calculate_expirer_health,
    generate_payment_intent_expiration_metrics,
)

NOW = datetime(
    2026,
    6,
    11,
    10,
    0,
    tzinfo=UTC,
)


def build_state() -> PaymentIntentExpirerState:
    return PaymentIntentExpirerState(
        worker_name="payment-intent-expirer",
        last_cycle_started_at=NOW - timedelta(seconds=5),
        last_success_at=NOW - timedelta(seconds=30),
        last_error_at=NOW - timedelta(seconds=120),
        last_error="temporary database failure",
        successful_cycles_total=10,
        failed_cycles_total=2,
        expired_payment_intents_total=7,
    )


def test_expirer_is_healthy_after_recent_success() -> None:
    state = build_state()

    assert (
        calculate_expirer_health(
            state,
            stale_after_seconds=180,
            now=NOW,
        )
        == WorkerHealthStatus.HEALTHY
    )


def test_expirer_is_degraded_when_latest_cycle_failed() -> None:
    state = build_state()
    state.last_error_at = NOW - timedelta(seconds=10)

    assert (
        calculate_expirer_health(
            state,
            stale_after_seconds=180,
            now=NOW,
        )
        == WorkerHealthStatus.DEGRADED
    )


def test_expirer_is_stale_when_success_is_too_old() -> None:
    state = build_state()
    state.last_success_at = NOW - timedelta(seconds=181)
    state.last_error_at = None
    state.last_error = None

    assert (
        calculate_expirer_health(
            state,
            stale_after_seconds=180,
            now=NOW,
        )
        == WorkerHealthStatus.STALE
    )


def test_generate_payment_intent_expiration_metrics() -> None:
    db = Mock()
    state = build_state()

    with patch(
        ("app.services.payment_intent_expiration_metrics.get_payment_intent_expirer_state"),
        return_value=state,
    ):
        result = generate_payment_intent_expiration_metrics(
            db=db,
            stale_after_seconds=180,
            now=NOW,
        )

    metrics = result.decode()

    assert (
        "euroledger_payment_intent_expiration_health{"
        'status="healthy",worker_name="payment-intent-expirer"} 1.0' in metrics
    )

    assert (
        "euroledger_payment_intent_expiration_cycles_total{"
        'result="success",worker_name="payment-intent-expirer"} 10.0' in metrics
    )

    assert (
        "euroledger_payment_intent_expiration_cycles_total{"
        'result="failed",worker_name="payment-intent-expirer"} 2.0' in metrics
    )

    assert (
        "euroledger_payment_intents_expired_total{"
        'worker_name="payment-intent-expirer"} 7.0' in metrics
    )

    assert (
        "euroledger_payment_intent_expiration_"
        "last_success_age_seconds{"
        'worker_name="payment-intent-expirer"} 30.0' in metrics
    )


def test_generate_metrics_without_expirer_state() -> None:
    db = Mock()

    with patch(
        ("app.services.payment_intent_expiration_metrics.get_payment_intent_expirer_state"),
        return_value=None,
    ):
        result = generate_payment_intent_expiration_metrics(
            db=db,
            stale_after_seconds=180,
            now=NOW,
        )

    metrics = result.decode()

    assert (
        "euroledger_payment_intent_expiration_health{"
        'status="not_started",worker_name="payment-intent-expirer"} 1.0' in metrics
    )

    assert (
        "euroledger_payment_intents_expired_total{"
        'worker_name="payment-intent-expirer"} 0.0' in metrics
    )
