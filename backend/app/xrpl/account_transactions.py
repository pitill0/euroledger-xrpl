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
) -> list[dict[str, Any]]:
    if not account:
        raise XrplAccountTransactionFetchError("XRPL account address is required.")

    request = AccountTx(
        account=account,
        ledger_index_min=-1,
        ledger_index_max=-1,
        binary=False,
        forward=False,
        limit=limit,
    )
    response = client.request(request)

    if not response.is_successful():
        raise XrplAccountTransactionFetchError(f"XRPL account_tx request failed: {response.result}")

    transactions = response.result.get("transactions", [])

    return [extract_transaction_payload(transaction) for transaction in transactions]


def extract_transaction_payload(transaction_entry: dict[str, Any]) -> dict[str, Any]:
    transaction = transaction_entry.get("tx")

    if transaction is None:
        transaction = transaction_entry.get("tx_json")

    if not isinstance(transaction, dict):
        raise XrplAccountTransactionFetchError(
            "XRPL account_tx transaction entry does not contain a transaction payload."
        )

    transaction_hash = transaction_entry.get("hash")
    if transaction_hash is not None and "hash" not in transaction:
        transaction["hash"] = transaction_hash

    return transaction
