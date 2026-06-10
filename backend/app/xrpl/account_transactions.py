from typing import Any

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx


class XrplAccountTransactionFetchError(RuntimeError):
    """Raised when XRPL account transactions cannot be fetched."""


def fetch_account_transactions(
    client: JsonRpcClient,
    account: str,
    *,
    limit: int = 20,
    ledger_index_min: int = -1,
) -> list[dict[str, Any]]:
    if not account:
        raise XrplAccountTransactionFetchError("XRPL account address is required.")

    request = AccountTx(
        account=account,
        ledger_index_min=ledger_index_min,
        ledger_index_max=-1,
        binary=False,
        forward=ledger_index_min >= 0,
        limit=limit,
    )
    response = client.request(request)

    if not response.is_successful():
        raise XrplAccountTransactionFetchError(f"XRPL account_tx request failed: {response.result}")

    transactions = response.result.get("transactions", [])

    return [extract_transaction_payload(transaction) for transaction in transactions]


def extract_transaction_payload(
    transaction_entry: dict[str, Any],
) -> dict[str, Any]:
    transaction = transaction_entry.get("tx")

    if transaction is None:
        transaction = transaction_entry.get("tx_json")

    if not isinstance(transaction, dict):
        raise XrplAccountTransactionFetchError(
            "XRPL account_tx transaction entry does not contain a transaction payload."
        )

    payload = dict(transaction)

    transaction_hash = transaction_entry.get("hash")
    if transaction_hash is not None and "hash" not in payload:
        payload["hash"] = transaction_hash

    ledger_index = transaction_entry.get("ledger_index")
    if ledger_index is None:
        ledger_index = payload.get("ledger_index")

    if ledger_index is not None:
        payload["_ledger_index"] = int(ledger_index)

    return payload
