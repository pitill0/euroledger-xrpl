from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.exceptions import InvalidPaymentIntentStatusTransitionError
from app.domain.payment_status import can_transition_payment_intent_status
from app.domain.references import generate_payment_reference
from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.repositories.payment_intents import (
    get_payment_intent_by_id,
    get_payment_intent_by_reference,
    save_payment_intent,
    update_payment_intent,
)
from app.schemas.payment_intent import PaymentIntentCreate


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
