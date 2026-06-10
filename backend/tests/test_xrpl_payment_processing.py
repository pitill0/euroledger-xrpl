from decimal import Decimal
from unittest.mock import Mock, patch

from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.schemas.payment_intent import PaymentIntentDetectedPayment
from app.xrpl.payments import process_xrpl_payment_transaction


def test_process_xrpl_payment_transaction_parses_and_confirms_payment() -> None:
    db = Mock()
    transaction = {
        "TransactionType": "Payment",
    }

    detected_payment = PaymentIntentDetectedPayment(
        reference="EL-ABC123DEF456",
        amount=Decimal("25.00"),
        currency="EUR",
        xrpl_transaction_hash="A" * 64,
        destination="rMerchantExpectedDestinationAddress",
        issuer="rIssuerAddress",
    )

    confirmed_payment_intent = PaymentIntent(
        reference="EL-ABC123DEF456",
        amount=Decimal("25.00"),
        currency="EUR",
        status=PaymentIntentStatus.confirmed,
        expected_destination="rMerchantExpectedDestinationAddress",
        xrpl_transaction_hash="A" * 64,
    )

    with (
        patch(
            "app.xrpl.payments.parse_xrpl_transaction_to_detected_payment",
            return_value=detected_payment,
        ) as parse_transaction,
        patch(
            "app.xrpl.payments.validate_and_confirm_detected_payment",
            return_value=confirmed_payment_intent,
        ) as validate_and_confirm,
    ):
        result = process_xrpl_payment_transaction(
            db=db,
            transaction=transaction,
        )

    parse_transaction.assert_called_once_with(transaction)
    validate_and_confirm.assert_called_once_with(
        db=db,
        detected_payment=detected_payment,
    )
    assert result == confirmed_payment_intent
