from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.workers.xrpl_payments import (
    UnsupportedXrplTransactionError,
    is_candidate_payment_transaction,
    process_candidate_xrpl_transaction,
)


def test_is_candidate_payment_transaction_accepts_payment_transaction() -> None:
    transaction = {
        "TransactionType": "Payment",
    }

    assert is_candidate_payment_transaction(transaction) is True


def test_is_candidate_payment_transaction_rejects_non_payment_transaction() -> None:
    transaction = {
        "TransactionType": "TrustSet",
    }

    assert is_candidate_payment_transaction(transaction) is False


def test_process_candidate_xrpl_transaction_processes_payment_transaction() -> None:
    db = Mock()
    transaction = {
        "TransactionType": "Payment",
    }

    confirmed_payment_intent = PaymentIntent(
        reference="EL-ABC123DEF456",
        amount=Decimal("25.00"),
        currency="EUR",
        status=PaymentIntentStatus.confirmed,
        expected_destination="rMerchantExpectedDestinationAddress",
        xrpl_transaction_hash="A" * 64,
    )

    with patch(
        "app.workers.xrpl_payments.process_xrpl_payment_transaction",
        return_value=confirmed_payment_intent,
    ) as process_payment:
        result = process_candidate_xrpl_transaction(
            db=db,
            transaction=transaction,
        )

    process_payment.assert_called_once_with(
        db=db,
        transaction=transaction,
    )
    assert result == confirmed_payment_intent


def test_process_candidate_xrpl_transaction_rejects_unsupported_transaction() -> None:
    db = Mock()
    transaction = {
        "TransactionType": "TrustSet",
    }

    with pytest.raises(UnsupportedXrplTransactionError):
        process_candidate_xrpl_transaction(
            db=db,
            transaction=transaction,
        )
