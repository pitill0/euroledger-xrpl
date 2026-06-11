from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.payment_intent_expirer_state import (
    PaymentIntentExpirerState,
)

PAYMENT_INTENT_EXPIRER_NAME = "payment-intent-expirer"


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_payment_intent_expirer_state(
    db: Session,
) -> PaymentIntentExpirerState | None:
    return db.get(
        PaymentIntentExpirerState,
        PAYMENT_INTENT_EXPIRER_NAME,
    )


def get_or_create_payment_intent_expirer_state(
    db: Session,
) -> PaymentIntentExpirerState:
    state = get_payment_intent_expirer_state(db)

    if state is not None:
        return state

    state = PaymentIntentExpirerState(
        worker_name=PAYMENT_INTENT_EXPIRER_NAME,
        successful_cycles_total=0,
        failed_cycles_total=0,
        expired_payment_intents_total=0,
    )

    db.add(state)
    db.commit()
    db.refresh(state)

    return state


def mark_payment_intent_expiration_cycle_started(
    db: Session,
    state: PaymentIntentExpirerState,
    *,
    started_at: datetime | None = None,
) -> PaymentIntentExpirerState:
    state.last_cycle_started_at = started_at or utc_now()

    db.commit()
    db.refresh(state)

    return state


def mark_payment_intent_expiration_cycle_succeeded(
    db: Session,
    state: PaymentIntentExpirerState,
    *,
    expired: int,
    succeeded_at: datetime | None = None,
) -> PaymentIntentExpirerState:
    state.last_success_at = succeeded_at or utc_now()
    state.successful_cycles_total += 1
    state.expired_payment_intents_total += expired

    db.commit()
    db.refresh(state)

    return state


def mark_payment_intent_expiration_cycle_failed(
    db: Session,
    state: PaymentIntentExpirerState,
    *,
    error: str,
    failed_at: datetime | None = None,
) -> PaymentIntentExpirerState:
    state.last_error_at = failed_at or utc_now()
    state.last_error = error
    state.failed_cycles_total += 1

    db.commit()
    db.refresh(state)

    return state
