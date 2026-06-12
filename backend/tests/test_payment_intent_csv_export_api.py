from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.domain.exceptions import (
    InvalidPaymentIntentListFilterError,
)
from app.main import app


def override_get_db():
    yield Mock()


def test_export_payment_intents_returns_csv() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                ("app.api.routes.payment_intents.validate_payment_intent_export_filters"),
            ) as validate_filters,
            patch(
                ("app.api.routes.payment_intents.stream_payment_intents_csv"),
                return_value=iter(
                    [
                        "\ufeff",
                        "id,reference\n",
                        "intent-id,EL-TEST\n",
                    ]
                ),
            ) as stream_csv,
        ):
            response = TestClient(app).get(
                "/payment-intents/export",
                params={
                    "status_filter": "pending",
                    "reference": "EL-TEST",
                    "max_rows": 250,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.text.lstrip("\ufeff") == ("id,reference\nintent-id,EL-TEST\n")

    assert response.headers["content-type"].startswith("text/csv")

    assert response.headers["content-disposition"].startswith(
        'attachment; filename="euroledger-payment-intents-'
    )

    assert response.headers["x-export-max-rows"] == "250"

    validate_filters.assert_called_once()

    call = stream_csv.call_args.kwargs

    assert call["status"] == "pending"
    assert call["reference"] == "EL-TEST"
    assert call["max_rows"] == 250


def test_export_invalid_date_interval_returns_422() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            ("app.api.routes.payment_intents.validate_payment_intent_export_filters"),
            side_effect=InvalidPaymentIntentListFilterError(
                "created_from must be earlier than or equal to created_to.",
            ),
        ):
            response = TestClient(app).get(
                "/payment-intents/export",
                params={
                    "created_from": ("2026-06-30T00:00:00Z"),
                    "created_to": ("2026-06-01T00:00:00Z"),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422

    assert response.json()["detail"] == (
        "created_from must be earlier than or equal to created_to."
    )


def test_export_rejects_max_rows_above_limit() -> None:
    response = TestClient(app).get(
        "/payment-intents/export",
        params={
            "max_rows": 10001,
        },
    )

    assert response.status_code == 422


def test_export_route_is_not_interpreted_as_id() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            ("app.api.routes.payment_intents.stream_payment_intents_csv"),
            return_value=iter(
                [
                    "\ufeff",
                    "id,reference\n",
                ]
            ),
        ):
            response = TestClient(app).get(
                "/payment-intents/export",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
