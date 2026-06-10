from decimal import Decimal
from unittest.mock import Mock, patch

from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.workers.xrpl_payments import UnsupportedXrplTransactionError
from app.workers.xrpl_scanner import scan_xrpl_transactions


def build_confirmed_payment_intent(reference: str) -> PaymentIntent:
    return PaymentIntent(
        reference=reference,
        amount=Decimal("25.00"),
        currency="EUR",
        status=PaymentIntentStatus.confirmed,
        expected_destination="rMerchantExpectedDestinationAddress",
        xrpl_transaction_hash="A" * 64,
    )


def test_scan_xrpl_transactions_processes_payment_transactions() -> None:
    db = Mock()
    transactions = [
        {"TransactionType": "Payment"},
        {"TransactionType": "Payment"},
    ]

    confirmed_payment_intents = [
        build_confirmed_payment_intent("EL-ABC123DEF456"),
        build_confirmed_payment_intent("EL-DEF456ABC123"),
    ]

    with patch(
        "app.workers.xrpl_scanner.process_candidate_xrpl_transaction",
        side_effect=confirmed_payment_intents,
    ) as process_transaction:
        result = scan_xrpl_transactions(
            db=db,
            transactions=transactions,
        )

    assert process_transaction.call_count == 2
    assert result.processed == 2
    assert result.skipped == 0
    assert result.failed == 0
    assert result.confirmed_payment_intents == confirmed_payment_intents
    assert result.errors == []


def test_scan_xrpl_transactions_skips_unsupported_transactions() -> None:
    db = Mock()
    transactions = [
        {"TransactionType": "TrustSet"},
    ]

    with patch(
        "app.workers.xrpl_scanner.process_candidate_xrpl_transaction",
        side_effect=UnsupportedXrplTransactionError,
    ):
        result = scan_xrpl_transactions(
            db=db,
            transactions=transactions,
        )

    assert result.processed == 0
    assert result.skipped == 1
    assert result.failed == 0
    assert result.confirmed_payment_intents == []
    assert result.errors == []


def test_scan_xrpl_transactions_records_failed_transactions() -> None:
    db = Mock()
    transactions = [
        {"TransactionType": "Payment"},
    ]

    with patch(
        "app.workers.xrpl_scanner.process_candidate_xrpl_transaction",
        side_effect=ValueError("Invalid XRPL transaction"),
    ):
        result = scan_xrpl_transactions(
            db=db,
            transactions=transactions,
        )

    assert result.processed == 0
    assert result.skipped == 0
    assert result.failed == 1
    assert result.confirmed_payment_intents == []
    assert result.errors == ["Invalid XRPL transaction"]


def test_scan_xrpl_transactions_continues_after_failure() -> None:
    db = Mock()
    transactions = [
        {"TransactionType": "Payment"},
        {"TransactionType": "Payment"},
        {"TransactionType": "TrustSet"},
    ]

    confirmed_payment_intent = build_confirmed_payment_intent("EL-ABC123DEF456")

    with patch(
        "app.workers.xrpl_scanner.process_candidate_xrpl_transaction",
        side_effect=[
            ValueError("Invalid XRPL transaction"),
            confirmed_payment_intent,
            UnsupportedXrplTransactionError,
        ],
    ):
        result = scan_xrpl_transactions(
            db=db,
            transactions=transactions,
        )

    assert result.processed == 1
    assert result.skipped == 1
    assert result.failed == 1
    assert result.confirmed_payment_intents == [confirmed_payment_intent]
    assert result.errors == ["Invalid XRPL transaction"]
