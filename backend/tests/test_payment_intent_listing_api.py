from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.domain.exceptions import (
    InvalidPaymentIntentCursorError,
)
from app.main import app
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.services.payment_intent_listing import (
    PaymentIntentListResult,
)

NOW = datetime(
    2026,
    6,
    12,
    16,
    0,
    tzinfo=UTC,
)


def build_payment_intent() -> PaymentIntent:
    return PaymentIntent(
        id="intent-id",
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=PaymentIntentStatus.pending,
        description="Order 123",
        expected_destination=None,
        xrpl_transaction_hash=None,
        expires_at=NOW + timedelta(minutes=15),
        cancelled_at=None,
        cancellation_reason=None,
        created_at=NOW,
        updated_at=NOW,
    )


def override_get_db():
    yield Mock()


def test_list_payment_intents_returns_page() -> None:
    app.dependency_overrides[get_db] = override_get_db

    result = PaymentIntentListResult(
        items=[build_payment_intent()],
        next_cursor="next-page",
    )

    try:
        with patch(
            ("app.api.routes.payment_intents.list_payment_intents"),
            return_value=result,
        ) as list_service:
            response = TestClient(app).get(
                "/payment-intents",
                params={
                    "status_filter": "pending",
                    "reference": "EL-TESTREFERENCE",
                    "created_from": ("2026-06-12T15:00:00Z"),
                    "created_to": ("2026-06-12T17:00:00Z"),
                    "limit": 10,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "intent-id"
    assert body["next_cursor"] == "next-page"

    call = list_service.call_args.kwargs

    assert call["status"] == PaymentIntentStatus.pending
    assert call["reference"] == "EL-TESTREFERENCE"
    assert call["limit"] == 10


def test_list_payment_intents_uses_defaults() -> None:
    app.dependency_overrides[get_db] = override_get_db

    result = PaymentIntentListResult(
        items=[],
        next_cursor=None,
    )

    try:
        with patch(
            ("app.api.routes.payment_intents.list_payment_intents"),
            return_value=result,
        ) as list_service:
            response = TestClient(app).get(
                "/payment-intents",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next_cursor": None,
    }

    call = list_service.call_args.kwargs

    assert call["status"] is None
    assert call["reference"] is None
    assert call["created_from"] is None
    assert call["created_to"] is None
    assert call["cursor"] is None
    assert call["limit"] == 20


def test_invalid_cursor_returns_422() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            ("app.api.routes.payment_intents.list_payment_intents"),
            side_effect=InvalidPaymentIntentCursorError(
                "Invalid payment intent pagination cursor.",
            ),
        ):
            response = TestClient(app).get(
                "/payment-intents",
                params={
                    "cursor": "invalid",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == ("Invalid payment intent pagination cursor.")


def test_invalid_status_returns_422() -> None:
    response = TestClient(app).get(
        "/payment-intents",
        params={
            "status_filter": "unknown",
        },
    )

    assert response.status_code == 422


def test_limit_above_maximum_returns_422() -> None:
    response = TestClient(app).get(
        "/payment-intents",
        params={
            "limit": 101,
        },
    )

    assert response.status_code == 422
