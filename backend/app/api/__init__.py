from fastapi import APIRouter

from app.api.routes import health, payment_intents

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(payment_intents.router)
