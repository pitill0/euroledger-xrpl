from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "EuroLedger XRPL"

    postgres_db: str = "euroledger"
    postgres_user: str = "euroledger"
    postgres_password: str = "euroledger"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    xrpl_network: str = "testnet"
    xrpl_rpc_url: str = "https://s.altnet.rippletest.net:51234"
    xrpl_websocket_url: str = "wss://s.altnet.rippletest.net:51233"

    demo_currency_code: str = "EUR"
    demo_currency_display: str = "EUR.demo"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
