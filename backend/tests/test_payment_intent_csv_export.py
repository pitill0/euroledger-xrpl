import csv
import io
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.domain.exceptions import (
    InvalidPaymentIntentListFilterError,
)
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.services.payment_intent_csv_export import (
    CSV_COLUMNS,
    stream_payment_intents_csv,
    validate_payment_intent_export_filters,
)

NOW = datetime(
    2026,
    6,
    12,
    17,
    0,
    tzinfo=UTC,
)


def build_payment_intent(
    *,
    payment_intent_id: str,
    created_at: datetime,
    status: PaymentIntentStatus = PaymentIntentStatus.pending,
) -> PaymentIntent:
    return PaymentIntent(
        id=payment_intent_id,
        reference=f"EL-{payment_intent_id.upper()}",
        amount=Decimal("25.00"),
        currency="EUR",
        status=status,
        description="CSV test",
        expected_destination=None,
        xrpl_transaction_hash=None,
        expires_at=created_at + timedelta(minutes=15),
        cancelled_at=None,
        cancellation_reason=None,
        created_at=created_at,
        updated_at=created_at,
    )


def parse_csv(
    chunks: list[str],
) -> list[list[str]]:
    content = "".join(chunks).lstrip("\ufeff")

    return list(
        csv.reader(
            io.StringIO(content),
        )
    )


def test_export_rejects_invalid_date_interval() -> None:
    with pytest.raises(
        InvalidPaymentIntentListFilterError,
        match="created_from",
    ):
        validate_payment_intent_export_filters(
            created_from=NOW,
            created_to=NOW - timedelta(minutes=1),
        )


def test_stream_exports_header_and_rows() -> None:
    db = Mock()

    first = build_payment_intent(
        payment_intent_id="intent-2",
        created_at=NOW,
    )

    second = build_payment_intent(
        payment_intent_id="intent-1",
        created_at=NOW - timedelta(minutes=1),
        status=PaymentIntentStatus.confirmed,
    )

    with patch(
        ("app.services.payment_intent_csv_export.list_payment_intents_repository"),
        return_value=(
            [first, second],
            False,
        ),
    ) as repository:
        chunks = list(
            stream_payment_intents_csv(
                db=db,
                status=None,
                reference=None,
                created_from=None,
                created_to=None,
                max_rows=1000,
            )
        )

    rows = parse_csv(chunks)

    assert rows[0] == list(CSV_COLUMNS)
    assert len(rows) == 3

    assert rows[1][0] == "intent-2"
    assert rows[1][1] == "EL-INTENT-2"
    assert rows[1][2] == "25.00"
    assert rows[1][4] == "pending"

    assert rows[2][0] == "intent-1"
    assert rows[2][4] == "confirmed"

    repository.assert_called_once_with(
        db=db,
        status=None,
        reference=None,
        created_from=None,
        created_to=None,
        cursor=None,
        limit=500,
    )


def test_stream_paginates_internally() -> None:
    db = Mock()

    first = build_payment_intent(
        payment_intent_id="intent-2",
        created_at=NOW,
    )

    second = build_payment_intent(
        payment_intent_id="intent-1",
        created_at=NOW - timedelta(minutes=1),
    )

    with patch(
        ("app.services.payment_intent_csv_export.list_payment_intents_repository"),
        side_effect=[
            ([first], True),
            ([second], False),
        ],
    ) as repository:
        chunks = list(
            stream_payment_intents_csv(
                db=db,
                status=PaymentIntentStatus.pending,
                reference=None,
                created_from=None,
                created_to=None,
                max_rows=1000,
            )
        )

    rows = parse_csv(chunks)

    assert len(rows) == 3
    assert repository.call_count == 2

    second_call = repository.call_args_list[1].kwargs

    assert second_call["cursor"] is not None
    assert second_call["cursor"].payment_intent_id == "intent-2"
    assert second_call["cursor"].created_at == NOW


def test_stream_respects_max_rows() -> None:
    db = Mock()

    items = [
        build_payment_intent(
            payment_intent_id=f"intent-{index}",
            created_at=NOW - timedelta(seconds=index),
        )
        for index in range(3)
    ]

    with patch(
        ("app.services.payment_intent_csv_export.list_payment_intents_repository"),
        return_value=(items[:2], True),
    ) as repository:
        chunks = list(
            stream_payment_intents_csv(
                db=db,
                status=None,
                reference=None,
                created_from=None,
                created_to=None,
                max_rows=2,
            )
        )

    rows = parse_csv(chunks)

    assert len(rows) == 3

    repository.assert_called_once_with(
        db=db,
        status=None,
        reference=None,
        created_from=None,
        created_to=None,
        cursor=None,
        limit=2,
    )


def test_empty_export_contains_only_header() -> None:
    db = Mock()

    with patch(
        ("app.services.payment_intent_csv_export.list_payment_intents_repository"),
        return_value=([], False),
    ):
        chunks = list(
            stream_payment_intents_csv(
                db=db,
                status=None,
                reference=None,
                created_from=None,
                created_to=None,
                max_rows=1000,
            )
        )

    rows = parse_csv(chunks)

    assert rows == [
        list(CSV_COLUMNS),
    ]
