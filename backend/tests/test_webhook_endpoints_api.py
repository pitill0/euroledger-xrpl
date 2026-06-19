from datetime import UTC, datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_merchant
from app.db.session import get_db
from app.main import app
from app.models.webhook import MerchantWebhookEndpoint

NOW = datetime(
    2026,
    6,
    19,
    13,
    45,
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


def build_webhook_endpoint(
    *,
    endpoint_id: str = "endpoint-id",
    merchant_id: str = MERCHANT_ID,
    url: str = "https://merchant.example.com/webhooks/euroledger",
    secret: str = "super-secret-value",
    enabled: bool = True,
) -> MerchantWebhookEndpoint:
    return MerchantWebhookEndpoint(
        id=endpoint_id,
        merchant_id=merchant_id,
        url=url,
        secret=secret,
        enabled=enabled,
        created_at=NOW,
        updated_at=NOW,
    )


def test_create_webhook_endpoint_requires_api_key() -> None:
    response = TestClient(app).post(
        "/webhook-endpoints",
        json={
            "url": "https://merchant.example.com/webhooks/euroledger",
            "secret": "super-secret-value",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key."


def test_create_webhook_endpoint_uses_authenticated_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    endpoint = build_webhook_endpoint()

    try:
        with patch(
            "app.api.routes.webhook_endpoints.create_webhook_endpoint",
            return_value=endpoint,
        ) as create_repository:
            response = TestClient(app).post(
                "/webhook-endpoints",
                json={
                    "url": "https://merchant.example.com/webhooks/euroledger",
                    "secret": "super-secret-value",
                    "enabled": True,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == "endpoint-id"
    assert body["merchant_id"] == MERCHANT_ID
    assert body["url"] == "https://merchant.example.com/webhooks/euroledger"
    assert body["enabled"] is True
    assert "secret" not in body

    call = create_repository.call_args.kwargs

    assert call["merchant_id"] == MERCHANT_ID
    assert call["url"] == "https://merchant.example.com/webhooks/euroledger"
    assert call["secret"] == "super-secret-value"
    assert call["enabled"] is True


def test_create_webhook_endpoint_rejects_invalid_url() -> None:
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        response = TestClient(app).post(
            "/webhook-endpoints",
            json={
                "url": "ftp://merchant.example.com/webhooks/euroledger",
                "secret": "super-secret-value",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_list_webhook_endpoints_is_scoped_to_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            "app.api.routes.webhook_endpoints.list_webhook_endpoints",
            return_value=[build_webhook_endpoint()],
        ) as list_repository:
            response = TestClient(app).get(
                "/webhook-endpoints",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert len(body["items"]) == 1
    assert body["items"][0]["merchant_id"] == MERCHANT_ID
    assert "secret" not in body["items"][0]

    assert list_repository.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_get_cross_merchant_webhook_endpoint_returns_not_found() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    try:
        with patch(
            "app.api.routes.webhook_endpoints.get_webhook_endpoint_by_id",
            return_value=None,
        ) as get_repository:
            response = TestClient(app).get(
                "/webhook-endpoints/other-merchant-endpoint",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Webhook endpoint not found"

    assert get_repository.call_args.kwargs["merchant_id"] == MERCHANT_ID


def test_patch_webhook_endpoint_updates_allowed_fields() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    endpoint = build_webhook_endpoint()

    try:
        with (
            patch(
                "app.api.routes.webhook_endpoints.get_webhook_endpoint_by_id",
                return_value=endpoint,
            ),
            patch(
                "app.api.routes.webhook_endpoints.update_webhook_endpoint",
                side_effect=lambda db, endpoint: endpoint,
            ) as update_repository,
        ):
            response = TestClient(app).patch(
                "/webhook-endpoints/endpoint-id",
                json={
                    "url": "https://merchant.example.com/new-webhook",
                    "enabled": False,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["url"] == "https://merchant.example.com/new-webhook"
    assert body["enabled"] is False
    assert "secret" not in body

    update_repository.assert_called_once()


def test_delete_webhook_endpoint_removes_endpoint() -> None:
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_merchant] = override_current_merchant

    endpoint = build_webhook_endpoint()

    try:
        with (
            patch(
                "app.api.routes.webhook_endpoints.get_webhook_endpoint_by_id",
                return_value=endpoint,
            ),
            patch(
                "app.api.routes.webhook_endpoints.delete_webhook_endpoint",
            ) as delete_repository,
        ):
            response = TestClient(app).delete(
                "/webhook-endpoints/endpoint-id",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""

    delete_repository.assert_called_once_with(
        db=delete_repository.call_args.kwargs["db"],
        endpoint=endpoint,
    )
