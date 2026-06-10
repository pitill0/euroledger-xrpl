from sqlalchemy.orm import Session

from app.models.payment_intent import PaymentIntent


def get_payment_intent_by_id(
    db: Session,
    payment_intent_id: str,
) -> PaymentIntent | None:
    return db.get(PaymentIntent, payment_intent_id)


def save_payment_intent(
    db: Session,
    payment_intent: PaymentIntent,
) -> PaymentIntent:
    db.add(payment_intent)
    db.commit()
    db.refresh(payment_intent)

    return payment_intent


def update_payment_intent(
    db: Session,
    payment_intent: PaymentIntent,
) -> PaymentIntent:
    db.commit()
    db.refresh(payment_intent)

    return payment_intent
