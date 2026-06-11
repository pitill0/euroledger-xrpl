from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app
from app.services.health_checks import DatabaseReadinessResult

client = TestClient(app)


def override_get_db():
    yield Mock()


def test_health_endpoint_remains_compatible() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "euroledger-xrpl-backend",
        "environment": "local",
    }


def test_liveness_endpoint() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "euroledger-xrpl-backend",
        "environment": "local",
    }


def test_readiness_endpoint_when_database_is_ready() -> None:
    app.dependency_overrides[get_db] = override_get_db

    readiness_result = DatabaseReadinessResult(
        database_reachable=True,
        migrations_current=True,
        current_revisions=("current-head",),
        expected_revisions=("current-head",),
    )

    try:
        with patch(
            "app.api.routes.health.check_database_readiness",
            return_value=readiness_result,
        ):
            response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "euroledger-xrpl-backend",
        "database": "available",
        "migrations": "current",
    }


def test_readiness_endpoint_when_migrations_are_outdated() -> None:
    app.dependency_overrides[get_db] = override_get_db

    readiness_result = DatabaseReadinessResult(
        database_reachable=True,
        migrations_current=False,
        current_revisions=("previous-head",),
        expected_revisions=("current-head",),
    )

    try:
        with patch(
            "app.api.routes.health.check_database_readiness",
            return_value=readiness_result,
        ):
            response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "euroledger-xrpl-backend",
        "database": "available",
        "migrations": "outdated",
        "current_revisions": ["previous-head"],
        "expected_revisions": ["current-head"],
    }


def test_readiness_endpoint_when_database_is_unavailable() -> None:
    app.dependency_overrides[get_db] = override_get_db

    database_error = OperationalError(
        statement="SELECT 1",
        params=None,
        orig=RuntimeError("database unavailable"),
    )

    try:
        with patch(
            "app.api.routes.health.check_database_readiness",
            side_effect=database_error,
        ):
            response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "euroledger-xrpl-backend",
        "database": "unavailable",
        "migrations": "unknown",
    }
