from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from prometheus_client.core import (
    CounterMetricFamily,
    GaugeMetricFamily,
    Metric,
)
from prometheus_client.exposition import generate_latest
from prometheus_client.registry import CollectorRegistry
from sqlalchemy.orm import Session

from app.models.payment_intent_expirer_state import (
    PaymentIntentExpirerState,
)
from app.repositories.payment_intent_expirer_states import (
    PAYMENT_INTENT_EXPIRER_NAME,
    get_payment_intent_expirer_state,
)
from app.schemas.worker_status import WorkerHealthStatus
from app.services.worker_status import ensure_utc

HEALTH_STATUSES = tuple(WorkerHealthStatus)


def calculate_expirer_health(
    state: PaymentIntentExpirerState | None,
    *,
    stale_after_seconds: int,
    now: datetime,
) -> WorkerHealthStatus:
    if state is None or state.last_cycle_started_at is None:
        return WorkerHealthStatus.NOT_STARTED

    if state.last_error_at is not None:
        last_error_at = ensure_utc(state.last_error_at)

        if state.last_success_at is None:
            return WorkerHealthStatus.DEGRADED

        if last_error_at > ensure_utc(state.last_success_at):
            return WorkerHealthStatus.DEGRADED

    if state.last_success_at is None:
        started_at = ensure_utc(state.last_cycle_started_at)

        if started_at < now - timedelta(seconds=stale_after_seconds):
            return WorkerHealthStatus.STALE

        return WorkerHealthStatus.NOT_STARTED

    last_success_at = ensure_utc(state.last_success_at)

    if last_success_at < now - timedelta(seconds=stale_after_seconds):
        return WorkerHealthStatus.STALE

    return WorkerHealthStatus.HEALTHY


class PaymentIntentExpirationMetricsCollector:
    def __init__(
        self,
        *,
        state: PaymentIntentExpirerState | None,
        status: WorkerHealthStatus,
        now: datetime,
    ) -> None:
        self.state = state
        self.status = status
        self.now = now

    def collect(self) -> Iterable[Metric]:
        yield self._build_health_metric()
        yield self._build_cycles_metric()
        yield self._build_expired_total_metric()
        yield self._build_last_success_timestamp_metric()
        yield self._build_last_error_timestamp_metric()
        yield self._build_last_success_age_metric()

    def _build_health_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            "euroledger_payment_intent_expiration_health",
            "Current health state of the payment intent expirer.",
            labels=["worker_name", "status"],
        )

        for status in HEALTH_STATUSES:
            metric.add_metric(
                [PAYMENT_INTENT_EXPIRER_NAME, status.value],
                1 if status == self.status else 0,
            )

        return metric

    def _build_cycles_metric(self) -> CounterMetricFamily:
        metric = CounterMetricFamily(
            "euroledger_payment_intent_expiration_cycles",
            "Total payment intent expiration cycles.",
            labels=["worker_name", "result"],
        )

        successful = 0
        failed = 0

        if self.state is not None:
            successful = self.state.successful_cycles_total
            failed = self.state.failed_cycles_total

        metric.add_metric(
            [PAYMENT_INTENT_EXPIRER_NAME, "success"],
            successful,
        )
        metric.add_metric(
            [PAYMENT_INTENT_EXPIRER_NAME, "failed"],
            failed,
        )

        return metric

    def _build_expired_total_metric(self) -> CounterMetricFamily:
        metric = CounterMetricFamily(
            "euroledger_payment_intents_expired",
            "Total number of automatically expired payment intents.",
            labels=["worker_name"],
        )

        value = 0

        if self.state is not None:
            value = self.state.expired_payment_intents_total

        metric.add_metric(
            [PAYMENT_INTENT_EXPIRER_NAME],
            value,
        )

        return metric

    def _build_last_success_timestamp_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            ("euroledger_payment_intent_expiration_last_success_timestamp_seconds"),
            "Unix timestamp of the last successful expiration cycle.",
            labels=["worker_name"],
        )

        value = 0.0

        if self.state is not None and self.state.last_success_at is not None:
            value = ensure_utc(self.state.last_success_at).timestamp()

        metric.add_metric(
            [PAYMENT_INTENT_EXPIRER_NAME],
            value,
        )

        return metric

    def _build_last_error_timestamp_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            ("euroledger_payment_intent_expiration_last_error_timestamp_seconds"),
            "Unix timestamp of the last failed expiration cycle.",
            labels=["worker_name"],
        )

        value = 0.0

        if self.state is not None and self.state.last_error_at is not None:
            value = ensure_utc(self.state.last_error_at).timestamp()

        metric.add_metric(
            [PAYMENT_INTENT_EXPIRER_NAME],
            value,
        )

        return metric

    def _build_last_success_age_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            ("euroledger_payment_intent_expiration_last_success_age_seconds"),
            "Age in seconds of the last successful expiration cycle.",
            labels=["worker_name"],
        )

        value = -1.0

        if self.state is not None and self.state.last_success_at is not None:
            value = max(
                0.0,
                (self.now - ensure_utc(self.state.last_success_at)).total_seconds(),
            )

        metric.add_metric(
            [PAYMENT_INTENT_EXPIRER_NAME],
            value,
        )

        return metric


def generate_payment_intent_expiration_metrics(
    db: Session,
    *,
    stale_after_seconds: int,
    now: datetime | None = None,
) -> bytes:
    current_time = now or datetime.now(UTC)
    state = get_payment_intent_expirer_state(db)

    status = calculate_expirer_health(
        state,
        stale_after_seconds=stale_after_seconds,
        now=current_time,
    )

    registry = CollectorRegistry()
    registry.register(
        PaymentIntentExpirationMetricsCollector(
            state=state,
            status=status,
            now=current_time,
        )
    )

    return generate_latest(registry)
