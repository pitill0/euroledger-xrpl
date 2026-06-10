from decimal import Decimal

import pytest

from app.xrpl.transactions import (
    XrplTransactionParseError,
    decode_hex_string,
    drops_to_xrp,
    parse_xrpl_transaction_to_detected_payment,
)

REFERENCE = "EL-ABC123DEF456"
REFERENCE_HEX = REFERENCE.encode("utf-8").hex().upper()
TRANSACTION_HASH = "A" * 64
DESTINATION = "rMerchantExpectedDestinationAddress"
ISSUER = "rIssuerAddress"


def test_parse_issued_currency_payment_transaction() -> None:
    transaction = {
        "TransactionType": "Payment",
        "Destination": DESTINATION,
        "Amount": {
            "currency": "EUR",
            "issuer": ISSUER,
            "value": "25.00",
        },
        "Memos": [
            {
                "Memo": {
                    "MemoData": REFERENCE_HEX,
                },
            },
        ],
        "hash": TRANSACTION_HASH,
    }

    detected_payment = parse_xrpl_transaction_to_detected_payment(transaction)

    assert detected_payment.reference == REFERENCE
    assert detected_payment.amount == Decimal("25.00")
    assert detected_payment.currency == "EUR"
    assert detected_payment.issuer == ISSUER
    assert detected_payment.destination == DESTINATION
    assert detected_payment.xrpl_transaction_hash == TRANSACTION_HASH


def test_parse_xrp_payment_transaction_from_drops() -> None:
    transaction = {
        "TransactionType": "Payment",
        "Destination": DESTINATION,
        "Amount": "25000000",
        "Memos": [
            {
                "Memo": {
                    "MemoData": REFERENCE_HEX,
                },
            },
        ],
        "hash": TRANSACTION_HASH,
    }

    detected_payment = parse_xrpl_transaction_to_detected_payment(transaction)

    assert detected_payment.reference == REFERENCE
    assert detected_payment.amount == Decimal("25")
    assert detected_payment.currency == "XRP"
    assert detected_payment.issuer is None
    assert detected_payment.destination == DESTINATION


def test_decode_hex_string() -> None:
    assert decode_hex_string(REFERENCE_HEX) == REFERENCE


def test_drops_to_xrp() -> None:
    assert drops_to_xrp("1500000") == Decimal("1.5")


def test_parser_rejects_missing_reference_memo() -> None:
    transaction = {
        "TransactionType": "Payment",
        "Destination": DESTINATION,
        "Amount": {
            "currency": "EUR",
            "issuer": ISSUER,
            "value": "25.00",
        },
        "hash": TRANSACTION_HASH,
    }

    with pytest.raises(XrplTransactionParseError):
        parse_xrpl_transaction_to_detected_payment(transaction)


def test_parser_rejects_invalid_hex_memo() -> None:
    transaction = {
        "TransactionType": "Payment",
        "Destination": DESTINATION,
        "Amount": {
            "currency": "EUR",
            "issuer": ISSUER,
            "value": "25.00",
        },
        "Memos": [
            {
                "Memo": {
                    "MemoData": "not-hex",
                },
            },
        ],
        "hash": TRANSACTION_HASH,
    }

    with pytest.raises(XrplTransactionParseError):
        parse_xrpl_transaction_to_detected_payment(transaction)


def test_parser_rejects_missing_destination() -> None:
    transaction = {
        "TransactionType": "Payment",
        "Amount": {
            "currency": "EUR",
            "issuer": ISSUER,
            "value": "25.00",
        },
        "Memos": [
            {
                "Memo": {
                    "MemoData": REFERENCE_HEX,
                },
            },
        ],
        "hash": TRANSACTION_HASH,
    }

    with pytest.raises(XrplTransactionParseError):
        parse_xrpl_transaction_to_detected_payment(transaction)


def test_parser_rejects_missing_hash() -> None:
    transaction = {
        "TransactionType": "Payment",
        "Destination": DESTINATION,
        "Amount": {
            "currency": "EUR",
            "issuer": ISSUER,
            "value": "25.00",
        },
        "Memos": [
            {
                "Memo": {
                    "MemoData": REFERENCE_HEX,
                },
            },
        ],
    }

    with pytest.raises(XrplTransactionParseError):
        parse_xrpl_transaction_to_detected_payment(transaction)
