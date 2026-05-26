from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="EuroLedger XRPL Backend",
    description=(
        "Testnet-first backend for euro-denominated payment intents, "
        "invoice references and XRPL settlement monitoring."
    ),
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "euroledger-xrpl-backend",
        "status": "running",
        "environment": settings.app_env,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "euroledger-xrpl-backend",
        "environment": settings.app_env,
    }
