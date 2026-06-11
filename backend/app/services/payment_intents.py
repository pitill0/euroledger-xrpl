from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.exceptions import (
    InvalidPaymentIntentStatusTransitionError,
    PaymentValidationError,
)
from app.domain.payment_status import can_transition_payment_intent_status
from app.domain.payment_validation import (
    validate_detected_payment_matches_intent,
)
from app.domain.references import generate_payment_reference
from app.models.payment_intent import (
    PaymentIntent,
    PaymentIntentStatus,
)
from app.repositories.payment_intents import (
    get_expired_pending_payment_intents,
    get_payment_intent_by_id,
    get_payment_intent_by_reference,
    save_payment_intent,
    update_payment_intent,
)
from app.schemas.payment_intent import (
    PaymentIntentCreate,
    PaymentIntentDetectedPayment,
)


@dataclass(frozen=True)
class PaymentIntentExpirationResult:
    expired: int
    limit: int


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_payment_intent(
    db: Session,
    payload: PaymentIntentCreate,
    *,
    now: datetime | None = None,
) -> PaymentIntent:
    created_at = now or utc_now()

    payment_intent = PaymentIntent(
        reference=generate_payment_reference(),
        amount=Decimal(payload.amount),
        currency=payload.currency.upper(),
        description=payload.description,
        expected_destination=payload.expected_destination,
        expires_at=created_at + timedelta(seconds=payload.expires_in_seconds),
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
    return get_payment_intent_by_reference(
        db,
        reference.upper(),
    )


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

    return update_payment_intent(
        db,
        payment_intent,
    )


def expire_pending_payment_intents(
    db: Session,
    *,
    limit: int,
    now: datetime | None = None,
) -> PaymentIntentExpirationResult:
    expires_before = now or utc_now()

    payment_intents = get_expired_pending_payment_intents(
        db=db,
        expires_before=expires_before,
        limit=limit,
    )

    for payment_intent in payment_intents:
        if not can_transition_payment_intent_status(
            payment_intent.status,
            PaymentIntentStatus.expired,
        ):
            continue

        payment_intent.status = PaymentIntentStatus.expired

    db.commit()

    return PaymentIntentExpirationResult(
        expired=len(payment_intents),
        limit=limit,
    )


def validate_and_confirm_detected_payment(
    db: Session,
    detected_payment: PaymentIntentDetectedPayment,
) -> PaymentIntent:
    payment_intent = get_payment_intent_by_payment_reference(
        db=db,
        reference=detected_payment.reference,
    )

    if payment_intent is None:
        raise PaymentValidationError(
            "Payment intent not found for detected payment reference.",
        )

    validate_detected_payment_matches_intent(
        payment_intent=payment_intent,
        detected_payment=detected_payment,
    )

    return confirm_payment_intent(
        db=db,
        payment_intent=payment_intent,
        xrpl_transaction_hash=detected_payment.xrpl_transaction_hash,
    )
