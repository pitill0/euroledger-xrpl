from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.health_checks import check_database_readiness

router = APIRouter(tags=["health"])

settings = get_settings()

DbSession = Annotated[Session, Depends(get_db)]


def build_live_response() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "euroledger-xrpl-backend",
        "environment": settings.app_env,
    }


@router.get("/health")
def health() -> dict[str, str]:
    return build_live_response()


@router.get("/health/live")
def liveness() -> dict[str, str]:
    return build_live_response()


@router.get("/health/ready")
def readiness(
    db: DbSession,
) -> JSONResponse:
    try:
        result = check_database_readiness(db)
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "euroledger-xrpl-backend",
                "database": "unavailable",
                "migrations": "unknown",
            },
        )

    if not result.migrations_current:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "euroledger-xrpl-backend",
                "database": "available",
                "migrations": "outdated",
                "current_revisions": list(result.current_revisions),
                "expected_revisions": list(result.expected_revisions),
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "service": "euroledger-xrpl-backend",
            "database": "available",
            "migrations": "current",
        },
    )
