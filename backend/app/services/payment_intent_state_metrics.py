from collections.abc import Iterable
from datetime import UTC, datetime

from prometheus_client.core import (
    GaugeMetricFamily,
    Metric,
)
from prometheus_client.exposition import generate_latest
from prometheus_client.registry import CollectorRegistry
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)

PAYMENT_INTENT_STATUSES = tuple(PaymentIntentStatus)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def get_payment_intent_status_counts(
    db: Session,
) -> dict[PaymentIntentStatus, int]:
    statement = select(
        PaymentIntent.status,
        func.count(PaymentIntent.id),
    ).group_by(PaymentIntent.status)

    result = {status: 0 for status in PAYMENT_INTENT_STATUSES}

    for status, count in db.execute(statement):
        normalized_status = (
            status if isinstance(status, PaymentIntentStatus) else PaymentIntentStatus(status)
        )

        result[normalized_status] = int(count)

    return result


def get_oldest_pending_created_at(
    db: Session,
) -> datetime | None:
    statement = select(
        func.min(PaymentIntent.created_at),
    ).where(
        PaymentIntent.status == PaymentIntentStatus.pending,
    )

    return db.execute(statement).scalar_one_or_none()


def get_past_due_pending_count(
    db: Session,
    *,
    now: datetime,
) -> int:
    statement = select(
        func.count(PaymentIntent.id),
    ).where(
        PaymentIntent.status == PaymentIntentStatus.pending,
        PaymentIntent.expires_at <= now,
    )

    return int(db.execute(statement).scalar_one())


class PaymentIntentStateMetricsCollector:
    def __init__(
        self,
        *,
        status_counts: dict[PaymentIntentStatus, int],
        oldest_pending_created_at: datetime | None,
        past_due_pending_count: int,
        now: datetime,
    ) -> None:
        self.status_counts = status_counts
        self.oldest_pending_created_at = oldest_pending_created_at
        self.past_due_pending_count = past_due_pending_count
        self.now = now

    def collect(self) -> Iterable[Metric]:
        yield self._build_status_metric()
        yield self._build_oldest_pending_age_metric()
        yield self._build_past_due_pending_metric()

    def _build_status_metric(self) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            "euroledger_payment_intents_by_status",
            "Current payment intent count grouped by status.",
            labels=["status"],
        )

        for status in PAYMENT_INTENT_STATUSES:
            metric.add_metric(
                [status.value],
                self.status_counts.get(status, 0),
            )

        return metric

    def _build_oldest_pending_age_metric(
        self,
    ) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            ("euroledger_payment_intent_oldest_pending_age_seconds"),
            ("Age in seconds of the oldest pending payment intent."),
        )

        value = 0.0

        if self.oldest_pending_created_at is not None:
            value = max(
                0.0,
                (self.now - ensure_utc(self.oldest_pending_created_at)).total_seconds(),
            )

        metric.add_metric([], value)

        return metric

    def _build_past_due_pending_metric(
        self,
    ) -> GaugeMetricFamily:
        metric = GaugeMetricFamily(
            ("euroledger_payment_intents_pending_past_due"),
            ("Current number of pending payment intents whose expiration time has passed."),
        )

        metric.add_metric(
            [],
            self.past_due_pending_count,
        )

        return metric


def generate_payment_intent_state_metrics(
    db: Session,
    *,
    now: datetime | None = None,
) -> bytes:
    current_time = now or datetime.now(UTC)

    registry = CollectorRegistry()
    registry.register(
        PaymentIntentStateMetricsCollector(
            status_counts=(get_payment_intent_status_counts(db)),
            oldest_pending_created_at=(get_oldest_pending_created_at(db)),
            past_due_pending_count=(
                get_past_due_pending_count(
                    db,
                    now=current_time,
                )
            ),
            now=current_time,
        )
    )

    return generate_latest(registry)
