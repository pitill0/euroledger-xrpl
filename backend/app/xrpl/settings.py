from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class XrplSettings:
    json_rpc_url: str
    merchant_address: str | None
    issuer_address: str | None
    currency_code: str


def build_xrpl_settings(settings: Settings) -> XrplSettings:
    return XrplSettings(
        json_rpc_url=settings.xrpl_json_rpc_url,
        merchant_address=settings.xrpl_merchant_address,
        issuer_address=settings.xrpl_issuer_address,
        currency_code=settings.xrpl_currency_code.upper(),
    )
