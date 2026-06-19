from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.webhook_delivery_worker_state import WebhookDeliveryWorkerState

WEBHOOK_DELIVERY_WORKER_NAME = "webhook-worker"


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_webhook_delivery_worker_state(
    db: Session,
) -> WebhookDeliveryWorkerState | None:
    return db.get(
        WebhookDeliveryWorkerState,
        WEBHOOK_DELIVERY_WORKER_NAME,
    )


def get_or_create_webhook_delivery_worker_state(
    db: Session,
) -> WebhookDeliveryWorkerState:
    state = get_webhook_delivery_worker_state(db)

    if state is not None:
        return state

    state = WebhookDeliveryWorkerState(
        worker_name=WEBHOOK_DELIVERY_WORKER_NAME,
        successful_cycles_total=0,
        failed_cycles_total=0,
        processed_deliveries_total=0,
        delivered_deliveries_total=0,
        failed_deliveries_total=0,
        discarded_deliveries_total=0,
    )

    db.add(state)
    db.commit()
    db.refresh(state)

    return state


def mark_webhook_delivery_cycle_started(
    db: Session,
    state: WebhookDeliveryWorkerState,
    *,
    started_at: datetime | None = None,
) -> WebhookDeliveryWorkerState:
    state.last_cycle_started_at = started_at or utc_now()

    db.commit()
    db.refresh(state)

    return state


def mark_webhook_delivery_cycle_succeeded(
    db: Session,
    state: WebhookDeliveryWorkerState,
    *,
    processed: int,
    delivered: int,
    failed: int,
    discarded: int,
    succeeded_at: datetime | None = None,
) -> WebhookDeliveryWorkerState:
    state.last_success_at = succeeded_at or utc_now()
    state.successful_cycles_total += 1
    state.processed_deliveries_total += processed
    state.delivered_deliveries_total += delivered
    state.failed_deliveries_total += failed
    state.discarded_deliveries_total += discarded

    db.commit()
    db.refresh(state)

    return state


def mark_webhook_delivery_cycle_failed(
    db: Session,
    state: WebhookDeliveryWorkerState,
    *,
    error: str,
    failed_at: datetime | None = None,
) -> WebhookDeliveryWorkerState:
    state.last_error_at = failed_at or utc_now()
    state.last_error = error
    state.failed_cycles_total += 1

    db.commit()
    db.refresh(state)

    return state
