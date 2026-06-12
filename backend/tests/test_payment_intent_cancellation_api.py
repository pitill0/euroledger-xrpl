from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.domain.exceptions import (
    InvalidPaymentIntentStatusTransitionError,
    PaymentIntentCancellationConflictError,
)
from app.main import app
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.services.payment_intents import (
    PaymentIntentCancellationResult,
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
    status: PaymentIntentStatus = PaymentIntentStatus.cancelled,
) -> PaymentIntent:
    return PaymentIntent(
        id="intent-id",
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=status,
        description="Order 123",
        expected_destination=None,
        xrpl_transaction_hash=None,
        expires_at=NOW + timedelta(minutes=15),
        cancelled_at=NOW if status == PaymentIntentStatus.cancelled else None,
        cancellation_reason=(
            "Customer request" if status == PaymentIntentStatus.cancelled else None
        ),
        created_at=NOW,
        updated_at=NOW,
    )


def override_get_db():
    yield Mock()


def test_cancel_payment_intent_returns_200() -> None:
    app.dependency_overrides[get_db] = override_get_db

    payment_intent = build_payment_intent()

    result = PaymentIntentCancellationResult(
        payment_intent=payment_intent,
        cancelled=True,
    )

    try:
        with (
            patch(
                "app.api.routes.payment_intents.get_payment_intent",
                return_value=payment_intent,
            ),
            patch(
                "app.api.routes.payment_intents.cancel_payment_intent",
                return_value=result,
            ) as cancel_service,
        ):
            response = TestClient(app).post(
                "/payment-intents/intent-id/cancel",
                json={
                    "reason": "Customer request",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancelled_at"] == NOW.isoformat().replace(
        "+00:00",
        "Z",
    )
    assert response.json()["cancellation_reason"] == "Customer request"

    cancel_service.assert_called_once_with(
        db=cancel_service.call_args.kwargs["db"],
        payment_intent=payment_intent,
        reason="Customer request",
    )


def test_cancel_payment_intent_replay_returns_200() -> None:
    app.dependency_overrides[get_db] = override_get_db

    payment_intent = build_payment_intent()

    result = PaymentIntentCancellationResult(
        payment_intent=payment_intent,
        cancelled=False,
    )

    try:
        with (
            patch(
                "app.api.routes.payment_intents.get_payment_intent",
                return_value=payment_intent,
            ),
            patch(
                "app.api.routes.payment_intents.cancel_payment_intent",
                return_value=result,
            ),
        ):
            response = TestClient(app).post(
                "/payment-intents/intent-id/cancel",
                json={
                    "reason": "Customer request",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_payment_intent_not_found() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.routes.payment_intents.get_payment_intent",
            return_value=None,
        ):
            response = TestClient(app).post(
                "/payment-intents/missing/cancel",
                json={
                    "reason": "Customer request",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment intent not found"


def test_cannot_cancel_confirmed_payment_intent() -> None:
    app.dependency_overrides[get_db] = override_get_db

    payment_intent = build_payment_intent(
        status=PaymentIntentStatus.confirmed,
    )

    try:
        with (
            patch(
                "app.api.routes.payment_intents.get_payment_intent",
                return_value=payment_intent,
            ),
            patch(
                "app.api.routes.payment_intents.cancel_payment_intent",
                side_effect=InvalidPaymentIntentStatusTransitionError(
                    "Cannot cancel payment intent from status 'confirmed'.",
                ),
            ),
        ):
            response = TestClient(app).post(
                "/payment-intents/intent-id/cancel",
                json={
                    "reason": "Customer request",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "Cannot cancel" in response.json()["detail"]


def test_cancellation_replay_with_different_reason_returns_409() -> None:
    app.dependency_overrides[get_db] = override_get_db

    payment_intent = build_payment_intent()

    try:
        with (
            patch(
                "app.api.routes.payment_intents.get_payment_intent",
                return_value=payment_intent,
            ),
            patch(
                "app.api.routes.payment_intents.cancel_payment_intent",
                side_effect=PaymentIntentCancellationConflictError(
                    "Payment intent was already cancelled with a different reason.",
                ),
            ),
        ):
            response = TestClient(app).post(
                "/payment-intents/intent-id/cancel",
                json={
                    "reason": "Duplicate order",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "different reason" in response.json()["detail"]
