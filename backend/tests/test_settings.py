from app.core.config import Settings


def test_database_url_is_built_from_postgres_settings() -> None:
    settings = Settings(
        _env_file=None,
        postgres_user="user",
        postgres_password="password",
        postgres_host="localhost",
        postgres_port=5433,
        postgres_db="database",
    )

    assert settings.database_url == ("postgresql+psycopg://user:password@localhost:5433/database")


def test_xrpl_settings_have_safe_defaults() -> None:
    settings = Settings(
        _env_file=None,
        xrpl_merchant_address=None,
        xrpl_issuer_address=None,
    )

    assert settings.xrpl_json_rpc_url == "https://s.altnet.rippletest.net:51234/"
    assert settings.xrpl_currency_code == "EUR"
    assert settings.xrpl_merchant_address is None
    assert settings.xrpl_issuer_address is None


def test_xrpl_currency_code_can_be_overridden() -> None:
    settings = Settings(
        _env_file=None,
        xrpl_currency_code="USD",
    )

    assert settings.xrpl_currency_code == "USD"


def test_empty_xrpl_addresses_are_normalized_to_none() -> None:
    settings = Settings(
        xrpl_merchant_address="",
        xrpl_issuer_address="",
    )

    assert settings.xrpl_merchant_address is None
    assert settings.xrpl_issuer_address is None
