from collections.abc import Iterable
from datetime import UTC, datetime

from prometheus_client.core import (
    CounterMetricFamily,
    GaugeMetricFamily,
    Metric,
)
from prometheus_client.exposition import generate_latest
from prometheus_client.registry import CollectorRegistry
from sqlalchemy.orm import Session

from app.models.worker_state import WorkerState
from app.repositories.worker_states import get_worker_state
from app.schemas.worker_status import WorkerHealthStatus
from app.services.worker_status import calculate_worker_health, ensure_utc
from app.workers.xrpl_sync import XRPL_PAYMENT_WORKER_NAME

HEALTH_STATUSES = tuple(WorkerHealthStatus)


class XrplWorkerMetricsCollector:
    def __init__(
        self,
        *,
        state: WorkerState | None,
        status: WorkerHealthStatus,
        now: datetime,
    ) -> None:
        self.state = state
        self.status = status
        self.now = now

    def collect(self) -> Iterable[Metric]:
        yield self._build_health_metric()
        yield self._build_last_ledger_metric()
        yield self._build_last_success_timestamp_metric()
        yield self._build_last_error_timestamp_metric()
        yield self._build_last_success_age_metric()
        yield self._build_cycle_counter()
        yield self._build_transaction_counter()

    def _build_health_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            "euroledger_xrpl_worker_health",
            "Current health state of the XRPL worker.",
            labels=["worker_name", "status"],
        )

        for status in HEALTH_STATUSES:
            metric.add_metric(
                [XRPL_PAYMENT_WORKER_NAME, status.value],
                1 if status == self.status else 0,
            )

        return metric

    def _build_last_ledger_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            "euroledger_xrpl_worker_last_ledger_index",
            "Last XRPL ledger index persisted by the worker.",
            labels=["worker_name"],
        )

        ledger_index = 0
        if self.state is not None and self.state.last_ledger_index is not None:
            ledger_index = self.state.last_ledger_index

        metric.add_metric(
            [XRPL_PAYMENT_WORKER_NAME],
            ledger_index,
        )

        return metric

    def _build_last_success_timestamp_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            "euroledger_xrpl_worker_last_success_timestamp_seconds",
            "Unix timestamp of the last successful XRPL worker cycle.",
            labels=["worker_name"],
        )

        value = 0.0
        if self.state is not None and self.state.last_success_at is not None:
            value = ensure_utc(self.state.last_success_at).timestamp()

        metric.add_metric(
            [XRPL_PAYMENT_WORKER_NAME],
            value,
        )

        return metric

    def _build_last_error_timestamp_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            "euroledger_xrpl_worker_last_error_timestamp_seconds",
            "Unix timestamp of the last failed XRPL worker cycle.",
            labels=["worker_name"],
        )

        value = 0.0
        if self.state is not None and self.state.last_error_at is not None:
            value = ensure_utc(self.state.last_error_at).timestamp()

        metric.add_metric(
            [XRPL_PAYMENT_WORKER_NAME],
            value,
        )

        return metric

    def _build_last_success_age_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            "euroledger_xrpl_worker_last_success_age_seconds",
            "Age in seconds of the last successful XRPL worker cycle.",
            labels=["worker_name"],
        )

        value = -1.0
        if self.state is not None and self.state.last_success_at is not None:
            last_success_at = ensure_utc(self.state.last_success_at)
            value = max(
                0.0,
                (self.now - last_success_at).total_seconds(),
            )

        metric.add_metric(
            [XRPL_PAYMENT_WORKER_NAME],
            value,
        )

        return metric

    def _build_cycle_counter(self) -> CounterMetricFamily:
        metric = CounterMetricFamily(
            "euroledger_xrpl_worker_cycles",
            "Total number of completed XRPL worker cycles.",
            labels=["worker_name", "result"],
        )

        successful = 0
        failed = 0

        if self.state is not None:
            successful = self.state.successful_cycles_total
            failed = self.state.failed_cycles_total

        metric.add_metric(
            [XRPL_PAYMENT_WORKER_NAME, "success"],
            successful,
        )
        metric.add_metric(
            [XRPL_PAYMENT_WORKER_NAME, "failed"],
            failed,
        )

        return metric

    def _build_transaction_counter(self) -> CounterMetricFamily:
        metric = CounterMetricFamily(
            "euroledger_xrpl_worker_transactions",
            "Total XRPL transactions handled by the worker.",
            labels=["worker_name", "result"],
        )

        values = {
            "fetched": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        }

        if self.state is not None:
            values = {
                "fetched": self.state.fetched_transactions_total,
                "processed": self.state.processed_transactions_total,
                "skipped": self.state.skipped_transactions_total,
                "failed": self.state.failed_transactions_total,
            }

        for result, value in values.items():
            metric.add_metric(
                [XRPL_PAYMENT_WORKER_NAME, result],
                value,
            )

        return metric


def generate_xrpl_worker_metrics(
    db: Session,
    *,
    stale_after_seconds: int,
    now: datetime | None = None,
) -> bytes:
    current_time = now or datetime.now(UTC)

    state = get_worker_state(
        db=db,
        worker_name=XRPL_PAYMENT_WORKER_NAME,
    )

    status = calculate_worker_health(
        state,
        stale_after_seconds=stale_after_seconds,
        now=current_time,
    )

    registry = CollectorRegistry()
    registry.register(
        XrplWorkerMetricsCollector(
            state=state,
            status=status,
            now=current_time,
        )
    )

    return generate_latest(registry)
