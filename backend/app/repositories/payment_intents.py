from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_intent import PaymentIntent, PaymentIntentStatus


def get_payment_intent_by_id(
    db: Session,
    payment_intent_id: str,
) -> PaymentIntent | None:
    return db.get(PaymentIntent, payment_intent_id)


def get_payment_intent_by_reference(
    db: Session,
    reference: str,
) -> PaymentIntent | None:
    statement = select(PaymentIntent).where(
        PaymentIntent.reference == reference,
    )

    return db.execute(statement).scalar_one_or_none()


def get_expired_pending_payment_intents(
    db: Session,
    *,
    expires_before: datetime,
    limit: int,
) -> list[PaymentIntent]:
    statement = (
        select(PaymentIntent)
        .where(
            PaymentIntent.status == PaymentIntentStatus.pending,
            PaymentIntent.expires_at <= expires_before,
        )
        .order_by(
            PaymentIntent.expires_at,
            PaymentIntent.id,
        )
        .limit(limit)
        .with_for_update(skip_locked=True)
    )

    return list(
        db.execute(statement).scalars().all(),
    )


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
