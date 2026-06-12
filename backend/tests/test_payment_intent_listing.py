from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from app.domain.exceptions import (
    InvalidPaymentIntentListFilterError,
)
from app.domain.payment_intent_pagination import (
    decode_payment_intent_cursor,
)
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.services.payment_intent_listing import (
    list_payment_intents,
)

NOW = datetime(
    2026,
    6,
    12,
    16,
    0,
    tzinfo=UTC,
)


def build_payment_intent(
    *,
    payment_intent_id: str,
    created_at: datetime,
) -> PaymentIntent:
    return PaymentIntent(
        id=payment_intent_id,
        reference=f"EL-{payment_intent_id}",
        amount="25.00",
        currency="EUR",
        status=PaymentIntentStatus.pending,
        expires_at=created_at + timedelta(minutes=15),
        cancelled_at=None,
        cancellation_reason=None,
        created_at=created_at,
        updated_at=created_at,
    )


def test_list_returns_items_without_cursor() -> None:
    db = Mock()

    items = [
        build_payment_intent(
            payment_intent_id="intent-2",
            created_at=NOW,
        ),
        build_payment_intent(
            payment_intent_id="intent-1",
            created_at=NOW - timedelta(minutes=1),
        ),
    ]

    with patch(
        ("app.services.payment_intent_listing.list_payment_intents_repository"),
        return_value=(items, False),
    ) as repository:
        result = list_payment_intents(
            db=db,
            status=PaymentIntentStatus.pending,
            reference=None,
            created_from=None,
            created_to=None,
            cursor=None,
            limit=20,
        )

    assert result.items == items
    assert result.next_cursor is None

    repository.assert_called_once_with(
        db=db,
        status=PaymentIntentStatus.pending,
        reference=None,
        created_from=None,
        created_to=None,
        cursor=None,
        limit=20,
    )


def test_list_returns_next_cursor() -> None:
    db = Mock()

    items = [
        build_payment_intent(
            payment_intent_id="intent-2",
            created_at=NOW,
        ),
        build_payment_intent(
            payment_intent_id="intent-1",
            created_at=NOW - timedelta(minutes=1),
        ),
    ]

    with patch(
        ("app.services.payment_intent_listing.list_payment_intents_repository"),
        return_value=(items, True),
    ):
        result = list_payment_intents(
            db=db,
            status=None,
            reference=None,
            created_from=None,
            created_to=None,
            cursor=None,
            limit=2,
        )

    assert result.next_cursor is not None

    decoded = decode_payment_intent_cursor(
        result.next_cursor,
    )

    assert decoded.payment_intent_id == "intent-1"
    assert decoded.created_at == (NOW - timedelta(minutes=1))


def test_created_from_after_created_to_fails() -> None:
    db = Mock()

    with pytest.raises(
        InvalidPaymentIntentListFilterError,
        match="created_from",
    ):
        list_payment_intents(
            db=db,
            status=None,
            reference=None,
            created_from=NOW,
            created_to=NOW - timedelta(minutes=1),
            cursor=None,
            limit=20,
        )
