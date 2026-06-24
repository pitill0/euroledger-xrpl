from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.models.webhook import WebhookDelivery

NOW = datetime(2026, 6, 22, 18, 0, tzinfo=UTC)


def override_get_db():
    yield Mock()


def build_payment_intent() -> PaymentIntent:
    return PaymentIntent(
        id="intent-123",
        merchant_id="merchant-123",
        reference="EL-TESTREFERENCE",
        amount=Decimal("5.00"),
        currency="EUR",
        status=PaymentIntentStatus.confirmed,
        description="WooCommerce order #19",
        expected_destination="rDestination",
        xrpl_transaction_hash="d" * 64,
        expires_at=NOW + timedelta(minutes=15),
        cancelled_at=None,
        cancellation_reason=None,
        created_at=NOW,
        updated_at=NOW,
    )


def build_delivery() -> WebhookDelivery:
    return WebhookDelivery(
        id="delivery-123",
        merchant_id="merchant-123",
        endpoint_id="endpoint-123",
        event_type="payment_intent.confirmed",
        payment_intent_id="intent-123",
        payload={},
        status="delivered",
        attempt_count=1,
        next_attempt_at=None,
        last_attempt_at=NOW,
        response_status_code=200,
        response_body='{"ok": true}',
        error_message=None,
        created_at=NOW,
        updated_at=NOW,
    )


def test_dashboard_requires_configured_token() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.routes.dashboard.get_settings",
            return_value=Mock(dashboard_token=None),
        ):
            response = TestClient(app).get(
                "/dashboard/payment-intents/intent-123",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Dashboard is not configured."


def test_dashboard_rejects_invalid_token() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.routes.dashboard.get_settings",
            return_value=Mock(dashboard_token="secret-token"),
        ):
            response = TestClient(app).get(
                "/dashboard/payment-intents/intent-123?token=wrong-token",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid dashboard token."


def test_dashboard_renders_payment_intent_and_deliveries() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                "app.api.routes.dashboard.get_settings",
                return_value=Mock(dashboard_token="secret-token"),
            ),
            patch(
                "app.api.routes.dashboard.get_payment_intent_by_id_unscoped",
                return_value=build_payment_intent(),
            ),
            patch(
                "app.api.routes.dashboard.list_webhook_deliveries_for_payment_intent",
                return_value=[build_delivery()],
            ),
        ):
            response = TestClient(app).get(
                "/dashboard/payment-intents/intent-123?token=secret-token",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "EL-TESTREFERENCE" in response.text
    assert "WooCommerce order #19" in response.text
    assert "payment_intent.confirmed" in response.text
    assert "status-confirmed" in response.text
    assert "status-delivered" in response.text


def test_dashboard_returns_404_for_missing_payment_intent() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                "app.api.routes.dashboard.get_settings",
                return_value=Mock(dashboard_token="secret-token"),
            ),
            patch(
                "app.api.routes.dashboard.get_payment_intent_by_id_unscoped",
                return_value=None,
            ),
        ):
            response = TestClient(app).get(
                "/dashboard/payment-intents/missing?token=secret-token",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment intent not found."
