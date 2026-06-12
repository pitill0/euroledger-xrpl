from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.domain.idempotency import (
    IdempotencyConflictError,
)
from app.main import app
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.services.payment_intents import (
    PaymentIntentCreationResult,
)

NOW = datetime(
    2026,
    6,
    12,
    10,
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
        cancelled_at=None,
        cancellation_reason=None,
        expires_at=NOW + timedelta(minutes=15),
        created_at=NOW,
        updated_at=NOW,
    )


def override_get_db():
    yield Mock()


def test_first_idempotent_request_returns_201() -> None:
    app.dependency_overrides[get_db] = override_get_db

    result = PaymentIntentCreationResult(
        payment_intent=build_payment_intent(),
        created=True,
    )

    try:
        with (
            patch(
                ("app.api.routes.payment_intents.create_payment_intent"),
                return_value=result,
            ) as create_service,
            patch(
                ("app.api.routes.payment_intents.record_payment_intent_creation"),
            ) as record_metric,
        ):
            client = TestClient(app)

            response = client.post(
                "/payment-intents",
                headers={
                    "Idempotency-Key": "order-123",
                },
                json={
                    "amount": "25.00",
                    "currency": "EUR",
                    "description": "Order 123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    assert create_service.call_args.kwargs["idempotency_key"] == "order-123"

    record_metric.assert_called_once_with(
        result="created",
        status_code=201,
        idempotent=True,
    )


def test_idempotent_replay_returns_200() -> None:
    app.dependency_overrides[get_db] = override_get_db

    result = PaymentIntentCreationResult(
        payment_intent=build_payment_intent(),
        created=False,
    )

    try:
        with (
            patch(
                ("app.api.routes.payment_intents.create_payment_intent"),
                return_value=result,
            ),
            patch(
                ("app.api.routes.payment_intents.record_payment_intent_creation"),
            ) as record_metric,
        ):
            client = TestClient(app)

            response = client.post(
                "/payment-intents",
                headers={
                    "Idempotency-Key": "order-123",
                },
                json={
                    "amount": "25.00",
                    "currency": "EUR",
                    "description": "Order 123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == "intent-id"
    assert response.json()["reference"] == "EL-TESTREFERENCE"

    record_metric.assert_called_once_with(
        result="replayed",
        status_code=200,
        idempotent=True,
    )


def test_idempotency_conflict_returns_409() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                ("app.api.routes.payment_intents.create_payment_intent"),
                side_effect=IdempotencyConflictError(
                    "Idempotency-Key has already been used with a different payload.",
                ),
            ),
            patch(
                ("app.api.routes.payment_intents.record_payment_intent_creation"),
            ) as record_metric,
        ):
            client = TestClient(app)

            response = client.post(
                "/payment-intents",
                headers={
                    "Idempotency-Key": "order-123",
                },
                json={
                    "amount": "30.00",
                    "currency": "EUR",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "different payload" in response.json()["detail"]

    record_metric.assert_called_once_with(
        result="conflict",
        status_code=409,
        idempotent=True,
    )


def test_creation_without_idempotency_key_remains_supported() -> None:
    app.dependency_overrides[get_db] = override_get_db

    result = PaymentIntentCreationResult(
        payment_intent=build_payment_intent(),
        created=True,
    )

    try:
        with (
            patch(
                ("app.api.routes.payment_intents.create_payment_intent"),
                return_value=result,
            ) as create_service,
            patch(
                ("app.api.routes.payment_intents.record_payment_intent_creation"),
            ) as record_metric,
        ):
            client = TestClient(app)

            response = client.post(
                "/payment-intents",
                json={
                    "amount": "25.00",
                    "currency": "EUR",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    assert create_service.call_args.kwargs["idempotency_key"] is None

    record_metric.assert_called_once_with(
        result="created",
        status_code=201,
        idempotent=False,
    )
