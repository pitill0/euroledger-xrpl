from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from app.models.webhook_delivery_worker_state import WebhookDeliveryWorkerState
from app.schemas.worker_status import WorkerHealthStatus
from app.services.webhook_delivery_metrics import (
    calculate_webhook_delivery_worker_health,
    generate_webhook_delivery_metrics,
)

NOW = datetime(
    2026,
    6,
    19,
    17,
    30,
    tzinfo=UTC,
)


def build_state() -> WebhookDeliveryWorkerState:
    return WebhookDeliveryWorkerState(
        worker_name="webhook-worker",
        last_cycle_started_at=NOW - timedelta(seconds=5),
        last_success_at=NOW - timedelta(seconds=30),
        last_error_at=NOW - timedelta(seconds=120),
        last_error="temporary network failure",
        successful_cycles_total=10,
        failed_cycles_total=2,
        processed_deliveries_total=25,
        delivered_deliveries_total=20,
        failed_deliveries_total=3,
        discarded_deliveries_total=2,
    )


def test_webhook_delivery_worker_is_healthy_after_recent_success() -> None:
    state = build_state()

    assert (
        calculate_webhook_delivery_worker_health(
            state,
            stale_after_seconds=180,
            now=NOW,
        )
        == WorkerHealthStatus.HEALTHY
    )


def test_webhook_delivery_worker_is_degraded_when_latest_cycle_failed() -> None:
    state = build_state()
    state.last_error_at = NOW - timedelta(seconds=10)

    assert (
        calculate_webhook_delivery_worker_health(
            state,
            stale_after_seconds=180,
            now=NOW,
        )
        == WorkerHealthStatus.DEGRADED
    )


def test_webhook_delivery_worker_is_stale_when_success_is_too_old() -> None:
    state = build_state()
    state.last_success_at = NOW - timedelta(seconds=181)
    state.last_error_at = None
    state.last_error = None

    assert (
        calculate_webhook_delivery_worker_health(
            state,
            stale_after_seconds=180,
            now=NOW,
        )
        == WorkerHealthStatus.STALE
    )


def test_generate_webhook_delivery_metrics() -> None:
    db = Mock()
    state = build_state()

    with patch(
        "app.services.webhook_delivery_metrics.get_webhook_delivery_worker_state",
        return_value=state,
    ):
        result = generate_webhook_delivery_metrics(
            db=db,
            stale_after_seconds=180,
            now=NOW,
        )

    metrics = result.decode()

    assert (
        "euroledger_webhook_delivery_worker_health{"
        'status="healthy",worker_name="webhook-worker"} 1.0' in metrics
    )

    assert (
        "euroledger_webhook_delivery_worker_cycles_total{"
        'result="success",worker_name="webhook-worker"} 10.0' in metrics
    )

    assert (
        "euroledger_webhook_deliveries_total{"
        'result="processed",worker_name="webhook-worker"} 25.0' in metrics
    )

    assert (
        "euroledger_webhook_deliveries_total{"
        'result="delivered",worker_name="webhook-worker"} 20.0' in metrics
    )

    assert (
        "euroledger_webhook_delivery_worker_last_success_age_seconds{"
        'worker_name="webhook-worker"} 30.0' in metrics
    )


def test_generate_metrics_without_webhook_delivery_worker_state() -> None:
    db = Mock()

    with patch(
        "app.services.webhook_delivery_metrics.get_webhook_delivery_worker_state",
        return_value=None,
    ):
        result = generate_webhook_delivery_metrics(
            db=db,
            stale_after_seconds=180,
            now=NOW,
        )

    metrics = result.decode()

    assert (
        "euroledger_webhook_delivery_worker_health{"
        'status="not_started",worker_name="webhook-worker"} 1.0' in metrics
    )

    assert (
        "euroledger_webhook_deliveries_total{"
        'result="processed",worker_name="webhook-worker"} 0.0' in metrics
    )
