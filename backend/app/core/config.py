from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"

    merchant_api_key_pepper: str = Field(
        default="local-development-only-change-me-before-production",
        min_length=32,
    )

    payment_intent_expirer_stale_after_seconds: int = 180
    webhook_delivery_worker_stale_after_seconds: int = 180
    dashboard_token: str | None = None

    postgres_user: str = "euroledger"
    postgres_password: str = "euroledger"
    postgres_db: str = "euroledger"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    xrpl_json_rpc_url: str = "https://s.altnet.rippletest.net:51234/"
    xrpl_merchant_address: str | None = None
    xrpl_issuer_address: str | None = None
    xrpl_currency_code: str = "EUR"

    xrpl_worker_stale_after_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "xrpl_merchant_address",
        "xrpl_issuer_address",
        "dashboard_token",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(
        cls,
        value: Any,
    ) -> Any:
        if value == "":
            return None

        return value

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
