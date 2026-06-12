import csv
import io
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.exceptions import (
    InvalidPaymentIntentListFilterError,
)
from app.domain.payment_intent_pagination import (
    PaymentIntentCursor,
)
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.repositories.payment_intents import (
    list_payment_intents as list_payment_intents_repository,
)

CSV_BATCH_SIZE = 500

CSV_COLUMNS = (
    "id",
    "merchant_id",
    "reference",
    "amount",
    "currency",
    "status",
    "description",
    "expected_destination",
    "xrpl_transaction_hash",
    "expires_at",
    "cancelled_at",
    "cancellation_reason",
    "created_at",
    "updated_at",
)


def ensure_utc(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def validate_payment_intent_export_filters(
    *,
    created_from: datetime | None,
    created_to: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    normalized_created_from = ensure_utc(
        created_from,
    )
    normalized_created_to = ensure_utc(
        created_to,
    )

    if (
        normalized_created_from is not None
        and normalized_created_to is not None
        and normalized_created_from > normalized_created_to
    ):
        raise InvalidPaymentIntentListFilterError(
            "created_from must be earlier than or equal to created_to.",
        )

    return (
        normalized_created_from,
        normalized_created_to,
    )


def serialize_datetime(
    value: datetime | None,
) -> str:
    normalized = ensure_utc(value)

    if normalized is None:
        return ""

    return normalized.isoformat().replace(
        "+00:00",
        "Z",
    )


def serialize_decimal(
    value: Decimal,
) -> str:
    return format(value, "f")


def payment_intent_to_csv_row(
    payment_intent: PaymentIntent,
) -> tuple[str, ...]:
    return (
        payment_intent.id,
        payment_intent.merchant_id,
        payment_intent.reference,
        serialize_decimal(payment_intent.amount),
        payment_intent.currency,
        payment_intent.status.value,
        payment_intent.description or "",
        payment_intent.expected_destination or "",
        payment_intent.xrpl_transaction_hash or "",
        serialize_datetime(payment_intent.expires_at),
        serialize_datetime(payment_intent.cancelled_at),
        payment_intent.cancellation_reason or "",
        serialize_datetime(payment_intent.created_at),
        serialize_datetime(payment_intent.updated_at),
    )


def render_csv_row(
    values: tuple[str, ...],
) -> str:
    output = io.StringIO(
        newline="",
    )

    writer = csv.writer(
        output,
        lineterminator="\n",
    )

    writer.writerow(values)

    return output.getvalue()


def stream_payment_intents_csv(
    db: Session,
    *,
    merchant_id: str,
    status: PaymentIntentStatus | None,
    reference: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    max_rows: int,
) -> Iterator[str]:
    (
        normalized_created_from,
        normalized_created_to,
    ) = validate_payment_intent_export_filters(
        created_from=created_from,
        created_to=created_to,
    )

    yield "\ufeff"
    yield render_csv_row(CSV_COLUMNS)

    exported_rows = 0
    cursor: PaymentIntentCursor | None = None

    while exported_rows < max_rows:
        remaining_rows = max_rows - exported_rows

        batch_limit = min(
            CSV_BATCH_SIZE,
            remaining_rows,
        )

        items, has_more = list_payment_intents_repository(
            db=db,
            merchant_id=merchant_id,
            status=status,
            reference=reference,
            created_from=normalized_created_from,
            created_to=normalized_created_to,
            cursor=cursor,
            limit=batch_limit,
        )

        if not items:
            break

        for payment_intent in items:
            yield render_csv_row(
                payment_intent_to_csv_row(
                    payment_intent,
                )
            )

            exported_rows += 1

            if exported_rows >= max_rows:
                break

        if exported_rows >= max_rows or not has_more:
            break

        last_item = items[-1]

        cursor = PaymentIntentCursor(
            created_at=last_item.created_at,
            payment_intent_id=last_item.id,
        )
