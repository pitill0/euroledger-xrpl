from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.worker_state import WorkerState


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_worker_state(
    db: Session,
    worker_name: str,
) -> WorkerState | None:
    return db.get(WorkerState, worker_name)


def get_or_create_worker_state(
    db: Session,
    worker_name: str,
) -> WorkerState:
    state = get_worker_state(db, worker_name)

    if state is not None:
        return state

    state = WorkerState(
        worker_name=worker_name,
        last_ledger_index=None,
    )

    db.add(state)
    db.commit()
    db.refresh(state)

    return state


def update_worker_ledger_cursor(
    db: Session,
    state: WorkerState,
    ledger_index: int,
) -> WorkerState:
    state.last_ledger_index = ledger_index

    db.commit()
    db.refresh(state)

    return state


def mark_worker_cycle_started(
    db: Session,
    state: WorkerState,
    *,
    started_at: datetime | None = None,
) -> WorkerState:
    state.last_cycle_started_at = started_at or utc_now()

    db.commit()
    db.refresh(state)

    return state


def mark_worker_cycle_succeeded(
    db: Session,
    state: WorkerState,
    *,
    succeeded_at: datetime | None = None,
) -> WorkerState:
    state.last_success_at = succeeded_at or utc_now()

    db.commit()
    db.refresh(state)

    return state


def mark_worker_cycle_failed(
    db: Session,
    state: WorkerState,
    error: str,
    *,
    failed_at: datetime | None = None,
) -> WorkerState:
    state.last_error_at = failed_at or utc_now()
    state.last_error = error

    db.commit()
    db.refresh(state)

    return state
