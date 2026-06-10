from app.core.config import Settings
from app.xrpl.settings import build_xrpl_settings


def test_build_xrpl_settings_from_app_settings() -> None:
    app_settings = Settings(
        xrpl_json_rpc_url="https://example.test/",
        xrpl_merchant_address="rMerchantAddress",
        xrpl_issuer_address="rIssuerAddress",
        xrpl_currency_code="eur",
    )

    xrpl_settings = build_xrpl_settings(app_settings)

    assert xrpl_settings.json_rpc_url == "https://example.test/"
    assert xrpl_settings.merchant_address == "rMerchantAddress"
    assert xrpl_settings.issuer_address == "rIssuerAddress"
    assert xrpl_settings.currency_code == "EUR"
