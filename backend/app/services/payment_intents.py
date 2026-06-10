from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.exceptions import InvalidPaymentIntentStatusTransitionError, PaymentValidationError
from app.domain.payment_status import can_transition_payment_intent_status
from app.domain.payment_validation import validate_detected_payment_matches_intent
from app.domain.references import generate_payment_reference
from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.repositories.payment_intents import (
    get_payment_intent_by_id,
    get_payment_intent_by_reference,
    save_payment_intent,
    update_payment_intent,
)
from app.schemas.payment_intent import PaymentIntentCreate, PaymentIntentDetectedPayment


def create_payment_intent(
    db: Session,
    payload: PaymentIntentCreate,
) -> PaymentIntent:
    payment_intent = PaymentIntent(
        reference=generate_payment_reference(),
        amount=Decimal(payload.amount),
        currency=payload.currency.upper(),
        description=payload.description,
    )

    return save_payment_intent(db, payment_intent)


def get_payment_intent(
    db: Session,
    payment_intent_id: str,
) -> PaymentIntent | None:
    return get_payment_intent_by_id(db, payment_intent_id)


def get_payment_intent_by_payment_reference(
    db: Session,
    reference: str,
) -> PaymentIntent | None:
    return get_payment_intent_by_reference(db, reference.upper())


def confirm_payment_intent(
    db: Session,
    payment_intent: PaymentIntent,
    xrpl_transaction_hash: str,
) -> PaymentIntent:
    if not can_transition_payment_intent_status(
        payment_intent.status,
        PaymentIntentStatus.confirmed,
    ):
        raise InvalidPaymentIntentStatusTransitionError(
            f"Cannot confirm payment intent from status '{payment_intent.status}'."
        )

    payment_intent.status = PaymentIntentStatus.confirmed
    payment_intent.xrpl_transaction_hash = xrpl_transaction_hash

    return update_payment_intent(db, payment_intent)


def validate_and_confirm_detected_payment(
    db: Session,
    detected_payment: PaymentIntentDetectedPayment,
) -> PaymentIntent:
    payment_intent = get_payment_intent_by_payment_reference(
        db=db,
        reference=detected_payment.reference,
    )

    if payment_intent is None:
        raise PaymentValidationError("Payment intent not found for detected payment reference.")

    validate_detected_payment_matches_intent(
        payment_intent=payment_intent,
        detected_payment=detected_payment,
    )

    return confirm_payment_intent(
        db=db,
        payment_intent=payment_intent,
        xrpl_transaction_hash=detected_payment.xrpl_transaction_hash,
    )
