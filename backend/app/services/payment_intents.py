from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.references import generate_payment_reference
from app.models.payment_intent import PaymentIntent
from app.repositories.payment_intents import get_payment_intent_by_id, save_payment_intent
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
