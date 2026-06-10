from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.exceptions import (
    InvalidPaymentIntentStatusTransitionError,
    PaymentValidationError,
)
from app.schemas.payment_intent import (
    PaymentIntentConfirm,
    PaymentIntentCreate,
    PaymentIntentDetectedPayment,
    PaymentIntentRead,
)
from app.services.payment_intents import (
    confirm_payment_intent,
    create_payment_intent,
    get_payment_intent,
    get_payment_intent_by_payment_reference,
    validate_and_confirm_detected_payment,
)

router = APIRouter(prefix="/payment-intents", tags=["payment-intents"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=PaymentIntentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_intent_endpoint(
    payload: PaymentIntentCreate,
    db: DbSession,
) -> PaymentIntentRead:
    return create_payment_intent(db, payload)


@router.post(
    "/detected-payments",
    response_model=PaymentIntentRead,
)
def validate_detected_payment_endpoint(
    payload: PaymentIntentDetectedPayment,
    db: DbSession,
) -> PaymentIntentRead:
    try:
        return validate_and_confirm_detected_payment(
            db=db,
            detected_payment=payload,
        )
    except PaymentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except InvalidPaymentIntentStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/by-reference/{reference}", response_model=PaymentIntentRead)
def get_payment_intent_by_reference_endpoint(
    reference: str,
    db: DbSession,
) -> PaymentIntentRead:
    payment_intent = get_payment_intent_by_payment_reference(db, reference)

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    return payment_intent


@router.get("/{payment_intent_id}", response_model=PaymentIntentRead)
def get_payment_intent_endpoint(
    payment_intent_id: str,
    db: DbSession,
) -> PaymentIntentRead:
    payment_intent = get_payment_intent(db, payment_intent_id)

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    return payment_intent


@router.post(
    "/{payment_intent_id}/confirm",
    response_model=PaymentIntentRead,
)
def confirm_payment_intent_endpoint(
    payment_intent_id: str,
    payload: PaymentIntentConfirm,
    db: DbSession,
) -> PaymentIntentRead:
    payment_intent = get_payment_intent(db, payment_intent_id)

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    try:
        return confirm_payment_intent(
            db=db,
            payment_intent=payment_intent,
            xrpl_transaction_hash=payload.xrpl_transaction_hash,
        )
    except InvalidPaymentIntentStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
