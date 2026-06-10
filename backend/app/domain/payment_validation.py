from decimal import Decimal

from app.domain.exceptions import PaymentValidationError
from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.schemas.payment_intent import PaymentIntentDetectedPayment


def normalize_amount(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"))


def validate_detected_payment_matches_intent(
    payment_intent: PaymentIntent,
    detected_payment: PaymentIntentDetectedPayment,
) -> None:
    if payment_intent.status != PaymentIntentStatus.pending:
        raise PaymentValidationError(
            f"Payment intent must be pending, current status is '{payment_intent.status}'."
        )

    if payment_intent.reference != detected_payment.reference.upper():
        raise PaymentValidationError("Detected payment reference does not match payment intent.")

    if normalize_amount(payment_intent.amount) != normalize_amount(detected_payment.amount):
        raise PaymentValidationError("Detected payment amount does not match payment intent.")

    if payment_intent.currency.upper() != detected_payment.currency.upper():
        raise PaymentValidationError("Detected payment currency does not match payment intent.")

    if not detected_payment.xrpl_transaction_hash:
        raise PaymentValidationError("Detected payment must include an XRPL transaction hash.")
