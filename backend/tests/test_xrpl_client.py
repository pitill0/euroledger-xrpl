from xrpl.clients import JsonRpcClient

from app.xrpl.client import build_xrpl_client
from app.xrpl.settings import XrplSettings


def test_build_xrpl_client_returns_json_rpc_client() -> None:
    xrpl_settings = XrplSettings(
        json_rpc_url="https://example.test/",
        merchant_address=None,
        issuer_address=None,
        currency_code="EUR",
    )

    client = build_xrpl_client(xrpl_settings)

    assert isinstance(client, JsonRpcClient)
