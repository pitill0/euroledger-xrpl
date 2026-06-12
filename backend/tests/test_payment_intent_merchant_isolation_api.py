from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_merchant
from app.db.session import get_db
from app.main import app
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.services.payment_intent_listing import (
    PaymentIntentListResult,
)
from app.services.payment_intents import (
    PaymentIntentCreationResult,
)

NOW = datetime(
    2026,
    6,
    12,
    19,
    0,
    tzinfo=UTC,
)

MERCHANT_ID = "merchant-a-id"
OTHER_MERCHANT_ID = "merchant-b-id"


def override_get_db():
    yield Mock()


def override_current_merchant():
    return Mock(
        id=MERCHANT_ID,
        slug="merchant-a",
    )


def build_payment_intent(
    *,
    merchant_id: str = MERCHANT_ID,
) -> PaymentIntent:
    return PaymentIntent(
        id="intent-id",
        merchant_id=merchant_id,
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=PaymentIntentStatus.pending,
        description="Merchant isolation test",
        expected_destination=None,
        xrpl_transaction_hash=None,
        expires_at=NOW + timedelta(minutes=15),
        cancelled_at=None,
        cancellation_reason=None,
        created_at=NOW,
        updated_at=NOW,
    )


def test_payment_intent_creation_requires_api_key() -> None:
    response = TestClient(app).post(
        "/payment-intents",
        json={
            "amount": "25.00",
            "currency": "EUR",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key."


def test_payment_intent_creation_uses_authenticated_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    result = PaymentIntentCreationResult(
        payment_intent=build_payment_intent(),
        created=True,
    )

    try:
        with (
            patch(
                "app.api.routes.payment_intents.create_payment_intent",
                return_value=result,
            ) as create_service,
            patch(
                ("app.api.routes.payment_intents.record_payment_intent_creation"),
            ),
        ):
            response = TestClient(app).post(
                "/payment-intents",
                json={
                    "amount": "25.00",
                    "currency": "EUR",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["merchant_id"] == MERCHANT_ID

    assert create_service.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_payment_intent_lookup_is_scoped_to_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            "app.api.routes.payment_intents.get_payment_intent",
            return_value=None,
        ) as get_service:
            response = TestClient(app).get(
                "/payment-intents/other-merchant-intent",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == ("Payment intent not found")

    assert get_service.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_reference_lookup_is_scoped_to_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            ("app.api.routes.payment_intents.get_payment_intent_by_payment_reference"),
            return_value=None,
        ) as get_service:
            response = TestClient(app).get(
                "/payment-intents/by-reference/EL-OTHERREFERENCE",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == ("Payment intent not found")

    assert get_service.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_payment_intent_listing_is_scoped_to_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    result = PaymentIntentListResult(
        items=[build_payment_intent()],
        next_cursor=None,
    )

    try:
        with patch(
            "app.api.routes.payment_intents.list_payment_intents",
            return_value=result,
        ) as list_service:
            response = TestClient(app).get(
                "/payment-intents",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["merchant_id"] == MERCHANT_ID

    assert list_service.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_payment_intent_export_is_scoped_to_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with (
            patch(
                ("app.api.routes.payment_intents.validate_payment_intent_export_filters"),
            ),
            patch(
                ("app.api.routes.payment_intents.stream_payment_intents_csv"),
                return_value=iter(
                    [
                        "\ufeff",
                        "id,merchant_id,reference\n",
                        (f"intent-id,{MERCHANT_ID},EL-TESTREFERENCE\n"),
                    ]
                ),
            ) as stream_service,
        ):
            response = TestClient(app).get(
                "/payment-intents/export",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert MERCHANT_ID in response.text
    assert OTHER_MERCHANT_ID not in response.text

    assert stream_service.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_cross_merchant_cancel_returns_not_found() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            "app.api.routes.payment_intents.get_payment_intent",
            return_value=None,
        ) as get_service:
            response = TestClient(app).post(
                "/payment-intents/other-merchant-intent/cancel",
                json={
                    "reason": "Customer request",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

    assert get_service.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_cross_merchant_confirm_returns_not_found() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            "app.api.routes.payment_intents.get_payment_intent",
            return_value=None,
        ) as get_service:
            response = TestClient(app).post(
                "/payment-intents/other-merchant-intent/confirm",
                json={
                    "xrpl_transaction_hash": "A" * 64,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

    assert get_service.call_args.kwargs["merchant_id"] == MERCHANT_ID
