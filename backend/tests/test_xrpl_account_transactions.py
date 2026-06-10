from unittest.mock import Mock

import pytest

from app.xrpl.account_transactions import (
    XrplAccountTransactionFetchError,
    extract_transaction_payload,
    fetch_account_transactions,
)


def test_fetch_account_transactions_requests_account_transactions() -> None:
    client = Mock()
    response = Mock()
    response.is_successful.return_value = True
    response.result = {
        "transactions": [
            {
                "tx": {
                    "TransactionType": "Payment",
                    "Destination": "rMerchantExpectedDestinationAddress",
                },
                "hash": "A" * 64,
            },
        ],
    }
    client.request.return_value = response

    transactions = fetch_account_transactions(
        client=client,
        account="rMerchantAddress",
        limit=10,
    )

    client.request.assert_called_once()
    request = client.request.call_args.args[0]

    assert request.account == "rMerchantAddress"
    assert request.limit == 10
    assert transactions == [
        {
            "TransactionType": "Payment",
            "Destination": "rMerchantExpectedDestinationAddress",
            "hash": "A" * 64,
        }
    ]


def test_fetch_account_transactions_rejects_missing_account() -> None:
    client = Mock()

    with pytest.raises(XrplAccountTransactionFetchError, match="address is required"):
        fetch_account_transactions(
            client=client,
            account="",
        )


def test_fetch_account_transactions_raises_on_unsuccessful_response() -> None:
    client = Mock()
    response = Mock()
    response.is_successful.return_value = False
    response.result = {
        "error": "actNotFound",
    }
    client.request.return_value = response

    with pytest.raises(XrplAccountTransactionFetchError, match="account_tx request failed"):
        fetch_account_transactions(
            client=client,
            account="rMerchantAddress",
        )


def test_extract_transaction_payload_supports_tx_json() -> None:
    transaction_entry = {
        "tx_json": {
            "TransactionType": "Payment",
            "Destination": "rMerchantExpectedDestinationAddress",
        },
        "hash": "B" * 64,
    }

    assert extract_transaction_payload(transaction_entry) == {
        "TransactionType": "Payment",
        "Destination": "rMerchantExpectedDestinationAddress",
        "hash": "B" * 64,
    }


def test_extract_transaction_payload_rejects_missing_payload() -> None:
    with pytest.raises(XrplAccountTransactionFetchError, match="transaction payload"):
        extract_transaction_payload(
            {
                "meta": {},
            }
        )
