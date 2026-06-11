from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.worker_state import WorkerState
from app.services.worker_metrics import generate_xrpl_worker_metrics

NOW = datetime(2026, 6, 11, 10, 0, tzinfo=UTC)


def build_worker_state() -> WorkerState:
    return WorkerState(
        worker_name="xrpl-payment-worker",
        last_ledger_index=123456,
        last_cycle_started_at=NOW - timedelta(seconds=5),
        last_success_at=NOW - timedelta(seconds=30),
        last_error_at=NOW - timedelta(seconds=120),
        last_error="temporary failure",
        successful_cycles_total=10,
        failed_cycles_total=2,
        fetched_transactions_total=25,
        processed_transactions_total=8,
        skipped_transactions_total=15,
        failed_transactions_total=2,
    )


def test_generate_metrics_for_healthy_worker() -> None:
    db = Mock()
    state = build_worker_state()

    with patch(
        "app.services.worker_metrics.get_worker_state",
        return_value=state,
    ):
        result = generate_xrpl_worker_metrics(
            db=db,
            stale_after_seconds=120,
            now=NOW,
        )

    metrics = result.decode()

    assert (
        "euroledger_xrpl_worker_health{"
        'status="healthy",worker_name="xrpl-payment-worker"} 1.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_health{"
        'status="degraded",worker_name="xrpl-payment-worker"} 0.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_last_ledger_index{"
        'worker_name="xrpl-payment-worker"} 123456.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_last_success_age_seconds{"
        'worker_name="xrpl-payment-worker"} 30.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_cycles_total{"
        'result="success",worker_name="xrpl-payment-worker"} 10.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_cycles_total{"
        'result="failed",worker_name="xrpl-payment-worker"} 2.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_transactions_total{"
        'result="processed",worker_name="xrpl-payment-worker"} 8.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_transactions_total{"
        'result="skipped",worker_name="xrpl-payment-worker"} 15.0' in metrics
    )


def test_generate_metrics_without_worker_state() -> None:
    db = Mock()

    with patch(
        "app.services.worker_metrics.get_worker_state",
        return_value=None,
    ):
        result = generate_xrpl_worker_metrics(
            db=db,
            stale_after_seconds=120,
            now=NOW,
        )

    metrics = result.decode()

    assert (
        "euroledger_xrpl_worker_health{"
        'status="not_started",worker_name="xrpl-payment-worker"} 1.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_last_success_age_seconds{"
        'worker_name="xrpl-payment-worker"} -1.0' in metrics
    )

    assert (
        "euroledger_xrpl_worker_cycles_total{"
        'result="success",worker_name="xrpl-payment-worker"} 0.0' in metrics
    )


def test_metrics_endpoint() -> None:
    db = Mock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.routes.metrics.generate_xrpl_worker_metrics",
            return_value=b"# HELP example_metric Example\nexample_metric 1\n",
        ):
            client = TestClient(app)
            response = client.get("/metrics")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.text == ("# HELP example_metric Example\nexample_metric 1\n")
    assert response.headers["content-type"].startswith("text/plain")
