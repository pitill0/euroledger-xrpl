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
        successful_cycles_total=0,
        failed_cycles_total=0,
        fetched_transactions_total=0,
        processed_transactions_total=0,
        skipped_transactions_total=0,
        failed_transactions_total=0,
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
    fetched: int,
    processed: int,
    skipped: int,
    failed: int,
    succeeded_at: datetime | None = None,
) -> WorkerState:
    state.last_success_at = succeeded_at or utc_now()
    state.successful_cycles_total += 1
    state.fetched_transactions_total += fetched
    state.processed_transactions_total += processed
    state.skipped_transactions_total += skipped
    state.failed_transactions_total += failed

    db.commit()
    db.refresh(state)

    return state


def mark_worker_cycle_failed(
    db: Session,
    state: WorkerState,
    error: str,
    *,
    fetched: int = 0,
    processed: int = 0,
    skipped: int = 0,
    failed: int = 0,
    failed_at: datetime | None = None,
) -> WorkerState:
    state.last_error_at = failed_at or utc_now()
    state.last_error = error
    state.failed_cycles_total += 1
    state.fetched_transactions_total += fetched
    state.processed_transactions_total += processed
    state.skipped_transactions_total += skipped
    state.failed_transactions_total += failed

    db.commit()
    db.refresh(state)

    return state
