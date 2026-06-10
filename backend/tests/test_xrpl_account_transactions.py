from unittest.mock import Mock

import pytest

from app.xrpl.account_transactions import (
    XrplAccountTransactionFetchError,
    extract_transaction_payload,
    fetch_account_transactions,
)


def build_successful_response(
    *,
    transactions: list[dict],
    marker: object | None = None,
) -> Mock:
    response = Mock()
    response.is_successful.return_value = True
    response.result = {
        "transactions": transactions,
    }

    if marker is not None:
        response.result["marker"] = marker

    return response


def test_fetch_account_transactions_requests_account_transactions() -> None:
    client = Mock()
    client.request.return_value = build_successful_response(
        transactions=[
            {
                "tx": {
                    "TransactionType": "Payment",
                    "Destination": "rMerchantAddress",
                },
                "hash": "A" * 64,
                "ledger_index": 100,
            },
        ],
    )

    transactions = fetch_account_transactions(
        client=client,
        account="rMerchantAddress",
        limit=10,
        ledger_index_min=50,
    )

    client.request.assert_called_once()

    request = client.request.call_args.args[0]

    assert request.account == "rMerchantAddress"
    assert request.limit == 10
    assert request.ledger_index_min == 50
    assert request.marker is None
    assert request.forward is True

    assert transactions == [
        {
            "TransactionType": "Payment",
            "Destination": "rMerchantAddress",
            "hash": "A" * 64,
            "_ledger_index": 100,
        }
    ]


def test_fetch_account_transactions_follows_pagination_marker() -> None:
    client = Mock()

    first_marker = {
        "ledger": 100,
        "seq": 1,
    }

    first_response = build_successful_response(
        transactions=[
            {
                "tx": {
                    "TransactionType": "Payment",
                },
                "hash": "A" * 64,
                "ledger_index": 100,
            },
        ],
        marker=first_marker,
    )

    second_response = build_successful_response(
        transactions=[
            {
                "tx_json": {
                    "TransactionType": "Payment",
                },
                "hash": "B" * 64,
                "ledger_index": 101,
            },
        ],
    )

    client.request.side_effect = [
        first_response,
        second_response,
    ]

    transactions = fetch_account_transactions(
        client=client,
        account="rMerchantAddress",
        limit=1,
        ledger_index_min=50,
    )

    assert client.request.call_count == 2

    first_request = client.request.call_args_list[0].args[0]
    second_request = client.request.call_args_list[1].args[0]

    assert first_request.marker is None
    assert second_request.marker == first_marker

    assert second_request.account == first_request.account
    assert second_request.limit == first_request.limit
    assert second_request.ledger_index_min == first_request.ledger_index_min
    assert second_request.ledger_index_max == first_request.ledger_index_max
    assert second_request.forward == first_request.forward

    assert transactions == [
        {
            "TransactionType": "Payment",
            "hash": "A" * 64,
            "_ledger_index": 100,
        },
        {
            "TransactionType": "Payment",
            "hash": "B" * 64,
            "_ledger_index": 101,
        },
    ]


def test_fetch_account_transactions_stops_when_marker_is_absent() -> None:
    client = Mock()
    client.request.return_value = build_successful_response(
        transactions=[],
    )

    transactions = fetch_account_transactions(
        client=client,
        account="rMerchantAddress",
    )

    assert transactions == []
    client.request.assert_called_once()


def test_fetch_account_transactions_rejects_missing_account() -> None:
    client = Mock()

    with pytest.raises(
        XrplAccountTransactionFetchError,
        match="address is required",
    ):
        fetch_account_transactions(
            client=client,
            account="",
        )

    client.request.assert_not_called()


def test_fetch_account_transactions_raises_on_unsuccessful_response() -> None:
    client = Mock()
    response = Mock()
    response.is_successful.return_value = False
    response.result = {
        "error": "actNotFound",
    }
    client.request.return_value = response

    with pytest.raises(
        XrplAccountTransactionFetchError,
        match="account_tx request failed",
    ):
        fetch_account_transactions(
            client=client,
            account="rMerchantAddress",
        )


def test_fetch_account_transactions_rejects_invalid_transactions_field() -> None:
    client = Mock()
    response = Mock()
    response.is_successful.return_value = True
    response.result = {
        "transactions": {
            "invalid": "value",
        },
    }
    client.request.return_value = response

    with pytest.raises(
        XrplAccountTransactionFetchError,
        match="invalid transactions field",
    ):
        fetch_account_transactions(
            client=client,
            account="rMerchantAddress",
        )


def test_extract_transaction_payload_supports_tx_json() -> None:
    transaction_entry = {
        "tx_json": {
            "TransactionType": "Payment",
            "Destination": "rMerchantAddress",
        },
        "hash": "B" * 64,
        "ledger_index": 123,
    }

    assert extract_transaction_payload(transaction_entry) == {
        "TransactionType": "Payment",
        "Destination": "rMerchantAddress",
        "hash": "B" * 64,
        "_ledger_index": 123,
    }


def test_extract_transaction_payload_does_not_mutate_source() -> None:
    source_transaction = {
        "TransactionType": "Payment",
    }

    transaction_entry = {
        "tx": source_transaction,
        "hash": "C" * 64,
        "ledger_index": 456,
    }

    payload = extract_transaction_payload(transaction_entry)

    assert payload["hash"] == "C" * 64
    assert payload["_ledger_index"] == 456
    assert source_transaction == {
        "TransactionType": "Payment",
    }


def test_extract_transaction_payload_rejects_missing_payload() -> None:
    with pytest.raises(
        XrplAccountTransactionFetchError,
        match="transaction payload",
    ):
        extract_transaction_payload(
            {
                "meta": {},
            }
        )
