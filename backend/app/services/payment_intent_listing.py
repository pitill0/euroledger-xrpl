from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.exceptions import (
    InvalidPaymentIntentListFilterError,
)
from app.domain.payment_intent_pagination import (
    PaymentIntentCursor,
    decode_payment_intent_cursor,
    encode_payment_intent_cursor,
)
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.repositories.payment_intents import (
    list_payment_intents as list_payment_intents_repository,
)


@dataclass(frozen=True)
class PaymentIntentListResult:
    items: list[PaymentIntent]
    next_cursor: str | None


def ensure_utc(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def list_payment_intents(
    db: Session,
    *,
    merchant_id: str,
    status: PaymentIntentStatus | None,
    reference: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    cursor: str | None,
    limit: int,
) -> PaymentIntentListResult:
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

    decoded_cursor = decode_payment_intent_cursor(cursor) if cursor is not None else None

    items, has_more = list_payment_intents_repository(
        db=db,
        merchant_id=merchant_id,
        status=status,
        reference=reference,
        created_from=normalized_created_from,
        created_to=normalized_created_to,
        cursor=decoded_cursor,
        limit=limit,
    )

    next_cursor: str | None = None

    if has_more and items:
        last_item = items[-1]

        next_cursor = encode_payment_intent_cursor(
            PaymentIntentCursor(
                created_at=last_item.created_at,
                payment_intent_id=last_item.id,
            )
        )

    return PaymentIntentListResult(
        items=items,
        next_cursor=next_cursor,
    )
