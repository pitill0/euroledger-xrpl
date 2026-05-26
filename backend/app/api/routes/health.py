from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()

settings = get_settings()


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "euroledger-xrpl-backend",
        "environment": settings.app_env,
    }
