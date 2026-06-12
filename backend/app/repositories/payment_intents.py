from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.domain.payment_intent_pagination import PaymentIntentCursor
from app.models.payment_intent import PaymentIntent, PaymentIntentStatus


def get_payment_intent_by_id(
    db: Session, payment_intent_id: str, *, merchant_id: str
) -> PaymentIntent | None:
    statement = select(PaymentIntent).where(
        PaymentIntent.id == payment_intent_id,
        PaymentIntent.merchant_id == merchant_id,
    )
    return db.execute(statement).scalar_one_or_none()


def get_payment_intent_by_reference(
    db: Session, reference: str, *, merchant_id: str
) -> PaymentIntent | None:
    statement = select(PaymentIntent).where(
        PaymentIntent.reference == reference,
        PaymentIntent.merchant_id == merchant_id,
    )
    return db.execute(statement).scalar_one_or_none()


def get_payment_intent_by_reference_unscoped(db: Session, reference: str) -> PaymentIntent | None:
    statement = select(PaymentIntent).where(PaymentIntent.reference == reference)
    return db.execute(statement).scalar_one_or_none()


def get_payment_intent_by_idempotency_key(
    db: Session, idempotency_key: str, *, merchant_id: str
) -> PaymentIntent | None:
    statement = select(PaymentIntent).where(
        PaymentIntent.idempotency_key == idempotency_key,
        PaymentIntent.merchant_id == merchant_id,
    )
    return db.execute(statement).scalar_one_or_none()


def list_payment_intents(
    db: Session,
    *,
    merchant_id: str,
    status: PaymentIntentStatus | None,
    reference: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    cursor: PaymentIntentCursor | None,
    limit: int,
) -> tuple[list[PaymentIntent], bool]:
    statement = select(PaymentIntent).where(PaymentIntent.merchant_id == merchant_id)
    if status is not None:
        statement = statement.where(PaymentIntent.status == status)
    if reference is not None:
        statement = statement.where(PaymentIntent.reference == reference.upper())
    if created_from is not None:
        statement = statement.where(PaymentIntent.created_at >= created_from)
    if created_to is not None:
        statement = statement.where(PaymentIntent.created_at <= created_to)
    if cursor is not None:
        statement = statement.where(
            or_(
                PaymentIntent.created_at < cursor.created_at,
                and_(
                    PaymentIntent.created_at == cursor.created_at,
                    PaymentIntent.id < cursor.payment_intent_id,
                ),
            )
        )
    statement = statement.order_by(PaymentIntent.created_at.desc(), PaymentIntent.id.desc()).limit(
        limit + 1
    )
    results = list(db.execute(statement).scalars().all())
    return results[:limit], len(results) > limit


def get_expired_pending_payment_intents(
    db: Session, *, expires_before: datetime, limit: int
) -> list[PaymentIntent]:
    statement = (
        select(PaymentIntent)
        .where(
            PaymentIntent.status == PaymentIntentStatus.pending,
            PaymentIntent.expires_at <= expires_before,
        )
        .order_by(PaymentIntent.expires_at, PaymentIntent.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list(db.execute(statement).scalars().all())


def save_payment_intent(db: Session, payment_intent: PaymentIntent) -> PaymentIntent:
    db.add(payment_intent)
    db.commit()
    db.refresh(payment_intent)
    return payment_intent


def update_payment_intent(db: Session, payment_intent: PaymentIntent) -> PaymentIntent:
    db.commit()
    db.refresh(payment_intent)
    return payment_intent
