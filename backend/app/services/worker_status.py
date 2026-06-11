from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.worker_state import WorkerState
from app.repositories.worker_states import get_worker_state
from app.schemas.worker_status import WorkerHealthStatus, WorkerStatusRead
from app.workers.xrpl_sync import XRPL_PAYMENT_WORKER_NAME


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def calculate_worker_health(
    state: WorkerState | None,
    *,
    stale_after_seconds: int,
    now: datetime | None = None,
) -> WorkerHealthStatus:
    current_time = now or datetime.now(UTC)

    if state is None or state.last_cycle_started_at is None:
        return WorkerHealthStatus.NOT_STARTED

    if state.last_error_at is not None:
        last_error_at = ensure_utc(state.last_error_at)

        if state.last_success_at is None:
            return WorkerHealthStatus.DEGRADED

        last_success_at = ensure_utc(state.last_success_at)

        if last_error_at > last_success_at:
            return WorkerHealthStatus.DEGRADED

    if state.last_success_at is None:
        started_at = ensure_utc(state.last_cycle_started_at)
        stale_before = current_time - timedelta(seconds=stale_after_seconds)

        if started_at < stale_before:
            return WorkerHealthStatus.STALE

        return WorkerHealthStatus.NOT_STARTED

    last_success_at = ensure_utc(state.last_success_at)
    stale_before = current_time - timedelta(seconds=stale_after_seconds)

    if last_success_at < stale_before:
        return WorkerHealthStatus.STALE

    return WorkerHealthStatus.HEALTHY


def get_xrpl_worker_status(
    db: Session,
    *,
    stale_after_seconds: int,
    now: datetime | None = None,
) -> WorkerStatusRead:
    state = get_worker_state(
        db=db,
        worker_name=XRPL_PAYMENT_WORKER_NAME,
    )

    status = calculate_worker_health(
        state,
        stale_after_seconds=stale_after_seconds,
        now=now,
    )

    if state is None:
        return WorkerStatusRead(
            worker_name=XRPL_PAYMENT_WORKER_NAME,
            status=status,
            last_ledger_index=None,
            last_cycle_started_at=None,
            last_success_at=None,
            last_error_at=None,
            last_error=None,
        )

    return WorkerStatusRead(
        worker_name=state.worker_name,
        status=status,
        last_ledger_index=state.last_ledger_index,
        last_cycle_started_at=state.last_cycle_started_at,
        last_success_at=state.last_success_at,
        last_error_at=state.last_error_at,
        last_error=state.last_error,
    )
