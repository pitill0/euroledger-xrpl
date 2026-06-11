from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.worker_state import WorkerState
from app.schemas.worker_status import WorkerHealthStatus
from app.services.worker_status import (
    calculate_worker_health,
    get_xrpl_worker_status,
)

NOW = datetime(2026, 6, 11, 10, 0, tzinfo=UTC)


def build_worker_state(
    *,
    last_cycle_started_at: datetime | None = NOW,
    last_success_at: datetime | None = None,
    last_error_at: datetime | None = None,
    last_error: str | None = None,
) -> WorkerState:
    return WorkerState(
        worker_name="xrpl-payment-worker",
        last_ledger_index=123,
        last_cycle_started_at=last_cycle_started_at,
        last_success_at=last_success_at,
        last_error_at=last_error_at,
        last_error=last_error,
    )


def test_worker_is_not_started_without_state() -> None:
    assert (
        calculate_worker_health(
            None,
            stale_after_seconds=120,
            now=NOW,
        )
        == WorkerHealthStatus.NOT_STARTED
    )


def test_worker_is_healthy_after_recent_success() -> None:
    state = build_worker_state(
        last_success_at=NOW - timedelta(seconds=30),
    )

    assert (
        calculate_worker_health(
            state,
            stale_after_seconds=120,
            now=NOW,
        )
        == WorkerHealthStatus.HEALTHY
    )


def test_worker_is_degraded_when_latest_cycle_failed() -> None:
    state = build_worker_state(
        last_success_at=NOW - timedelta(seconds=60),
        last_error_at=NOW - timedelta(seconds=10),
        last_error="temporary XRPL failure",
    )

    assert (
        calculate_worker_health(
            state,
            stale_after_seconds=120,
            now=NOW,
        )
        == WorkerHealthStatus.DEGRADED
    )


def test_worker_recovers_when_success_is_newer_than_error() -> None:
    state = build_worker_state(
        last_success_at=NOW - timedelta(seconds=10),
        last_error_at=NOW - timedelta(seconds=60),
        last_error="temporary XRPL failure",
    )

    assert (
        calculate_worker_health(
            state,
            stale_after_seconds=120,
            now=NOW,
        )
        == WorkerHealthStatus.HEALTHY
    )


def test_worker_is_stale_when_last_success_is_too_old() -> None:
    state = build_worker_state(
        last_success_at=NOW - timedelta(seconds=121),
    )

    assert (
        calculate_worker_health(
            state,
            stale_after_seconds=120,
            now=NOW,
        )
        == WorkerHealthStatus.STALE
    )


def test_get_xrpl_worker_status_returns_persisted_state() -> None:
    db = Mock()
    state = build_worker_state(
        last_success_at=NOW - timedelta(seconds=30),
    )

    with patch(
        "app.services.worker_status.get_worker_state",
        return_value=state,
    ):
        result = get_xrpl_worker_status(
            db=db,
            stale_after_seconds=120,
            now=NOW,
        )

    assert result.worker_name == "xrpl-payment-worker"
    assert result.status == WorkerHealthStatus.HEALTHY
    assert result.last_ledger_index == 123
    assert result.last_success_at == NOW - timedelta(seconds=30)


def test_worker_status_endpoint() -> None:
    db = Mock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    mocked_result = {
        "worker_name": "xrpl-payment-worker",
        "status": "healthy",
        "last_ledger_index": 123,
        "last_cycle_started_at": NOW,
        "last_success_at": NOW,
        "last_error_at": None,
        "last_error": None,
    }

    try:
        with patch(
            "app.api.routes.worker_status.get_xrpl_worker_status",
            return_value=mocked_result,
        ):
            client = TestClient(app)
            response = client.get("/worker-status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "worker_name": "xrpl-payment-worker",
        "status": "healthy",
        "last_ledger_index": 123,
        "last_cycle_started_at": "2026-06-11T10:00:00Z",
        "last_success_at": "2026-06-11T10:00:00Z",
        "last_error_at": None,
        "last_error": None,
    }
