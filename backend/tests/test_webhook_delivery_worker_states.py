from datetime import UTC, datetime
from unittest.mock import Mock

from app.models.webhook_delivery_worker_state import WebhookDeliveryWorkerState
from app.repositories.webhook_delivery_worker_states import (
    WEBHOOK_DELIVERY_WORKER_NAME,
    get_or_create_webhook_delivery_worker_state,
    mark_webhook_delivery_cycle_failed,
    mark_webhook_delivery_cycle_started,
    mark_webhook_delivery_cycle_succeeded,
)

NOW = datetime(
    2026,
    6,
    19,
    17,
    0,
    tzinfo=UTC,
)


def build_state() -> WebhookDeliveryWorkerState:
    return WebhookDeliveryWorkerState(
        worker_name=WEBHOOK_DELIVERY_WORKER_NAME,
        successful_cycles_total=1,
        failed_cycles_total=1,
        processed_deliveries_total=3,
        delivered_deliveries_total=1,
        failed_deliveries_total=1,
        discarded_deliveries_total=1,
    )


def test_get_or_create_webhook_delivery_worker_state_creates_missing_state() -> None:
    db = Mock()
    db.get.return_value = None

    state = get_or_create_webhook_delivery_worker_state(db)

    assert state.worker_name == WEBHOOK_DELIVERY_WORKER_NAME
    assert state.successful_cycles_total == 0
    assert state.failed_cycles_total == 0
    assert state.processed_deliveries_total == 0
    assert state.delivered_deliveries_total == 0
    assert state.failed_deliveries_total == 0
    assert state.discarded_deliveries_total == 0

    db.add.assert_called_once_with(state)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(state)


def test_mark_webhook_delivery_cycle_started() -> None:
    db = Mock()
    state = build_state()

    mark_webhook_delivery_cycle_started(
        db=db,
        state=state,
        started_at=NOW,
    )

    assert state.last_cycle_started_at == NOW
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(state)


def test_mark_webhook_delivery_cycle_succeeded() -> None:
    db = Mock()
    state = build_state()

    mark_webhook_delivery_cycle_succeeded(
        db=db,
        state=state,
        processed=10,
        delivered=8,
        failed=1,
        discarded=1,
        succeeded_at=NOW,
    )

    assert state.last_success_at == NOW
    assert state.successful_cycles_total == 2
    assert state.processed_deliveries_total == 13
    assert state.delivered_deliveries_total == 9
    assert state.failed_deliveries_total == 2
    assert state.discarded_deliveries_total == 2

    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(state)


def test_mark_webhook_delivery_cycle_failed() -> None:
    db = Mock()
    state = build_state()

    mark_webhook_delivery_cycle_failed(
        db=db,
        state=state,
        error="database unavailable",
        failed_at=NOW,
    )

    assert state.last_error_at == NOW
    assert state.last_error == "database unavailable"
    assert state.failed_cycles_total == 2

    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(state)
