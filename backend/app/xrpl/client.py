from xrpl.clients import JsonRpcClient

from app.xrpl.settings import XrplSettings


def build_xrpl_client(settings: XrplSettings) -> JsonRpcClient:
    return JsonRpcClient(settings.json_rpc_url)
