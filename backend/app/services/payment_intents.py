from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.exceptions import (
    InvalidPaymentIntentStatusTransitionError,
    PaymentIntentCancellationConflictError,
    PaymentValidationError,
)
from app.domain.idempotency import (
    IdempotencyConflictError,
    build_payment_intent_fingerprint,
)
from app.domain.payment_status import (
    can_transition_payment_intent_status,
)
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
    get_payment_intent_by_idempotency_key,
    get_payment_intent_by_reference,
    save_payment_intent,
    update_payment_intent,
)
from app.schemas.payment_intent import (
    PaymentIntentCreate,
    PaymentIntentDetectedPayment,
)


@dataclass(frozen=True)
class PaymentIntentCreationResult:
    payment_intent: PaymentIntent
    created: bool


@dataclass(frozen=True)
class PaymentIntentCancellationResult:
    payment_intent: PaymentIntent
    cancelled: bool


@dataclass(frozen=True)
class PaymentIntentExpirationResult:
    expired: int
    limit: int


def utc_now() -> datetime:
    return datetime.now(UTC)


def validate_idempotent_reuse(
    payment_intent: PaymentIntent,
    *,
    fingerprint: str,
) -> None:
    if payment_intent.idempotency_fingerprint != fingerprint:
        raise IdempotencyConflictError(
            "Idempotency-Key has already been used with a different payload.",
        )


def get_existing_idempotent_payment_intent(
    db: Session,
    *,
    idempotency_key: str,
    fingerprint: str,
) -> PaymentIntent | None:
    payment_intent = get_payment_intent_by_idempotency_key(
        db=db,
        idempotency_key=idempotency_key,
    )

    if payment_intent is None:
        return None

    validate_idempotent_reuse(
        payment_intent,
        fingerprint=fingerprint,
    )

    return payment_intent


def create_payment_intent(
    db: Session,
    payload: PaymentIntentCreate,
    *,
    idempotency_key: str | None = None,
    now: datetime | None = None,
) -> PaymentIntentCreationResult:
    created_at = now or utc_now()

    fingerprint: str | None = None

    if idempotency_key is not None:
        fingerprint = build_payment_intent_fingerprint(payload)

        existing_payment_intent = get_existing_idempotent_payment_intent(
            db=db,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
        )

        if existing_payment_intent is not None:
            return PaymentIntentCreationResult(
                payment_intent=existing_payment_intent,
                created=False,
            )

    payment_intent = PaymentIntent(
        reference=generate_payment_reference(),
        amount=Decimal(payload.amount),
        currency=payload.currency.upper(),
        description=payload.description,
        expected_destination=payload.expected_destination,
        expires_at=created_at
        + timedelta(
            seconds=payload.expires_in_seconds,
        ),
        idempotency_key=idempotency_key,
        idempotency_fingerprint=fingerprint,
    )

    try:
        payment_intent = save_payment_intent(
            db,
            payment_intent,
        )
    except IntegrityError:
        db.rollback()

        if idempotency_key is None or fingerprint is None:
            raise

        concurrent_payment_intent = get_existing_idempotent_payment_intent(
            db=db,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
        )

        if concurrent_payment_intent is None:
            raise

        return PaymentIntentCreationResult(
            payment_intent=concurrent_payment_intent,
            created=False,
        )

    return PaymentIntentCreationResult(
        payment_intent=payment_intent,
        created=True,
    )


def get_payment_intent(
    db: Session,
    payment_intent_id: str,
) -> PaymentIntent | None:
    return get_payment_intent_by_id(
        db,
        payment_intent_id,
    )


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


def cancel_payment_intent(
    db: Session,
    payment_intent: PaymentIntent,
    *,
    reason: str | None,
    now: datetime | None = None,
) -> PaymentIntentCancellationResult:
    if payment_intent.status == PaymentIntentStatus.cancelled:
        if payment_intent.cancellation_reason != reason:
            raise PaymentIntentCancellationConflictError(
                "Payment intent was already cancelled with a different reason.",
            )

        return PaymentIntentCancellationResult(
            payment_intent=payment_intent,
            cancelled=False,
        )

    if not can_transition_payment_intent_status(
        payment_intent.status,
        PaymentIntentStatus.cancelled,
    ):
        raise InvalidPaymentIntentStatusTransitionError(
            f"Cannot cancel payment intent from status '{payment_intent.status}'."
        )

    payment_intent.status = PaymentIntentStatus.cancelled
    payment_intent.cancelled_at = now or utc_now()
    payment_intent.cancellation_reason = reason

    payment_intent = update_payment_intent(
        db,
        payment_intent,
    )

    return PaymentIntentCancellationResult(
        payment_intent=payment_intent,
        cancelled=True,
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
