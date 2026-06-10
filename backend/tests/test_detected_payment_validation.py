from decimal import Decimal

import pytest

from app.domain.exceptions import PaymentValidationError
from app.domain.payment_validation import validate_detected_payment_matches_intent
from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.schemas.payment_intent import PaymentIntentDetectedPayment

XRPL_TRANSACTION_HASH = "A" * 64


def build_payment_intent(
    *,
    amount: str = "25.00",
    currency: str = "EUR",
    reference: str = "EL-ABC123DEF456",
    status: PaymentIntentStatus = PaymentIntentStatus.pending,
) -> PaymentIntent:
    return PaymentIntent(
        reference=reference,
        amount=Decimal(amount),
        currency=currency,
        status=status,
    )


def build_detected_payment(
    *,
    amount: str = "25.00",
    currency: str = "EUR",
    reference: str = "EL-ABC123DEF456",
) -> PaymentIntentDetectedPayment:
    return PaymentIntentDetectedPayment(
        reference=reference,
        amount=Decimal(amount),
        currency=currency,
        xrpl_transaction_hash=XRPL_TRANSACTION_HASH,
    )


def test_detected_payment_matches_pending_payment_intent() -> None:
    payment_intent = build_payment_intent()
    detected_payment = build_detected_payment()

    validate_detected_payment_matches_intent(payment_intent, detected_payment)


def test_detected_payment_reference_is_normalized_to_uppercase() -> None:
    payment_intent = build_payment_intent(reference="EL-ABC123DEF456")
    detected_payment = build_detected_payment(reference="el-abc123def456")

    validate_detected_payment_matches_intent(payment_intent, detected_payment)


def test_detected_payment_rejects_amount_mismatch() -> None:
    payment_intent = build_payment_intent(amount="25.00")
    detected_payment = build_detected_payment(amount="24.99")

    with pytest.raises(PaymentValidationError):
        validate_detected_payment_matches_intent(payment_intent, detected_payment)


def test_detected_payment_rejects_currency_mismatch() -> None:
    payment_intent = build_payment_intent(currency="EUR")
    detected_payment = build_detected_payment(currency="USD")

    with pytest.raises(PaymentValidationError):
        validate_detected_payment_matches_intent(payment_intent, detected_payment)


@pytest.mark.parametrize(
    "status",
    [
        PaymentIntentStatus.confirmed,
        PaymentIntentStatus.expired,
        PaymentIntentStatus.cancelled,
    ],
)
def test_detected_payment_rejects_non_pending_payment_intent(
    status: PaymentIntentStatus,
) -> None:
    payment_intent = build_payment_intent(status=status)
    detected_payment = build_detected_payment()

    with pytest.raises(PaymentValidationError):
        validate_detected_payment_matches_intent(payment_intent, detected_payment)
