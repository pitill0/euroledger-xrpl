from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_merchant
from app.db.session import get_db
from app.main import app
from app.models.webhook import WebhookDelivery, WebhookDeliveryStatus

NOW = datetime(
    2026,
    6,
    19,
    19,
    0,
    tzinfo=UTC,
)

MERCHANT_ID = "merchant-a-id"


def override_get_db():
    yield Mock()


def override_current_merchant():
    return Mock(
        id=MERCHANT_ID,
        slug="merchant-a",
    )


def build_webhook_delivery(
    *,
    delivery_id: str = "delivery-id",
    merchant_id: str = MERCHANT_ID,
    status: WebhookDeliveryStatus = WebhookDeliveryStatus.failed,
) -> WebhookDelivery:
    return WebhookDelivery(
        id=delivery_id,
        merchant_id=merchant_id,
        endpoint_id="endpoint-id",
        event_type="payment_intent.confirmed",
        payment_intent_id="intent-id",
        payload={
            "type": "payment_intent.confirmed",
            "data": {
                "object": {
                    "id": "intent-id",
                },
            },
        },
        status=status,
        attempt_count=2,
        next_attempt_at=NOW + timedelta(minutes=5),
        last_attempt_at=NOW,
        response_status_code=500,
        response_body="temporary failure",
        error_message="Webhook endpoint returned HTTP 500.",
        created_at=NOW - timedelta(minutes=10),
        updated_at=NOW,
    )


def test_list_webhook_deliveries_requires_api_key() -> None:
    response = TestClient(app).get(
        "/webhook-deliveries",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key."


def test_list_webhook_deliveries_is_scoped_to_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    delivery = build_webhook_delivery()

    try:
        with patch(
            "app.api.routes.webhook_deliveries.list_webhook_deliveries",
            return_value=[delivery],
        ) as list_repository:
            response = TestClient(app).get(
                "/webhook-deliveries",
                params={
                    "status_filter": "failed",
                    "event_type": "payment_intent.confirmed",
                    "payment_intent_id": "intent-id",
                    "endpoint_id": "endpoint-id",
                    "limit": 10,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "delivery-id"
    assert body["items"][0]["merchant_id"] == MERCHANT_ID
    assert body["items"][0]["status"] == "failed"
    assert body["items"][0]["attempt_count"] == 2
    assert body["items"][0]["response_status_code"] == 500
    assert body["items"][0]["response_body"] == "temporary failure"
    assert body["items"][0]["error_message"] == "Webhook endpoint returned HTTP 500."

    call = list_repository.call_args.kwargs

    assert call["merchant_id"] == MERCHANT_ID
    assert call["status"] == WebhookDeliveryStatus.failed
    assert call["event_type"] == "payment_intent.confirmed"
    assert call["payment_intent_id"] == "intent-id"
    assert call["endpoint_id"] == "endpoint-id"
    assert call["limit"] == 10


def test_list_webhook_deliveries_uses_defaults() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            "app.api.routes.webhook_deliveries.list_webhook_deliveries",
            return_value=[],
        ) as list_repository:
            response = TestClient(app).get(
                "/webhook-deliveries",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
    }

    call = list_repository.call_args.kwargs

    assert call["merchant_id"] == MERCHANT_ID
    assert call["status"] is None
    assert call["event_type"] is None
    assert call["payment_intent_id"] is None
    assert call["endpoint_id"] is None
    assert call["limit"] == 20


def test_get_webhook_delivery_returns_delivery() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    delivery = build_webhook_delivery()

    try:
        with patch(
            "app.api.routes.webhook_deliveries.get_webhook_delivery_by_id",
            return_value=delivery,
        ) as get_repository:
            response = TestClient(app).get(
                "/webhook-deliveries/delivery-id",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == "delivery-id"
    assert response.json()["merchant_id"] == MERCHANT_ID

    get_repository.assert_called_once_with(
        db=get_repository.call_args.kwargs["db"],
        delivery_id="delivery-id",
        merchant_id=MERCHANT_ID,
    )


def test_get_cross_merchant_webhook_delivery_returns_not_found() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            "app.api.routes.webhook_deliveries.get_webhook_delivery_by_id",
            return_value=None,
        ) as get_repository:
            response = TestClient(app).get(
                "/webhook-deliveries/other-merchant-delivery",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Webhook delivery not found"

    assert get_repository.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_invalid_webhook_delivery_status_returns_422() -> None:
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        response = TestClient(app).get(
            "/webhook-deliveries",
            params={
                "status_filter": "unknown",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_webhook_delivery_limit_above_maximum_returns_422() -> None:
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        response = TestClient(app).get(
            "/webhook-deliveries",
            params={
                "limit": 101,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
