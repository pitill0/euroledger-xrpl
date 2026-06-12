from fastapi import APIRouter

from app.api.routes import (
    auth,
    health,
    metrics,
    payment_intents,
    worker_status,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(payment_intents.router)
api_router.include_router(worker_status.router)
api_router.include_router(metrics.router)
