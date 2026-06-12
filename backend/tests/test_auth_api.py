from datetime import UTC, datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.merchant import Merchant

NOW = datetime(
    2026,
    6,
    12,
    18,
    0,
    tzinfo=UTC,
)


def override_get_db():
    yield Mock()


def build_merchant() -> Merchant:
    return Merchant(
        id="merchant-id",
        name="Test Merchant",
        slug="test-merchant",
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def test_auth_me_requires_api_key() -> None:
    response = TestClient(app).get(
        "/auth/me",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == ("Missing API key.")

    assert response.headers["www-authenticate"] == "ApiKey"


def test_auth_me_rejects_invalid_api_key() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            ("app.api.dependencies.auth.authenticate_merchant_api_key"),
            return_value=None,
        ):
            response = TestClient(app).get(
                "/auth/me",
                headers={
                    "X-API-Key": "elk_invalid_invalid",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == ("Invalid API key.")


def test_auth_me_returns_authenticated_merchant() -> None:
    app.dependency_overrides[get_db] = override_get_db

    merchant = build_merchant()

    try:
        with patch(
            ("app.api.dependencies.auth.authenticate_merchant_api_key"),
            return_value=merchant,
        ) as authenticate:
            response = TestClient(app).get(
                "/auth/me",
                headers={
                    "X-API-Key": ("elk_0123456789ab_abcdefghijklmnopqrstuvwxyzABCDEFGH"),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "merchant": {
            "id": "merchant-id",
            "name": "Test Merchant",
            "slug": "test-merchant",
            "is_active": True,
            "created_at": NOW.isoformat().replace(
                "+00:00",
                "Z",
            ),
            "updated_at": NOW.isoformat().replace(
                "+00:00",
                "Z",
            ),
        },
        "authentication_method": "api_key",
    }

    authenticate.assert_called_once()
