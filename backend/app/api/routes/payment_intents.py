from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate, PaymentIntentRead

router = APIRouter(prefix="/payment-intents", tags=["payment-intents"])


def generate_payment_reference() -> str:
    return f"EL-{uuid4().hex[:12].upper()}"


@router.post(
    "",
    response_model=PaymentIntentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_intent(
    payload: PaymentIntentCreate,
    db: Session = Depends(get_db),
) -> PaymentIntent:
    payment_intent = PaymentIntent(
        reference=generate_payment_reference(),
        amount=Decimal(payload.amount),
        currency=payload.currency.upper(),
        description=payload.description,
    )

    db.add(payment_intent)
    db.commit()
    db.refresh(payment_intent)

    return payment_intent


@router.get("/{payment_intent_id}", response_model=PaymentIntentRead)
def get_payment_intent(
    payment_intent_id: str,
    db: Session = Depends(get_db),
) -> PaymentIntent:
    payment_intent = db.get(PaymentIntent, payment_intent_id)

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found",
        )

    return payment_intent
