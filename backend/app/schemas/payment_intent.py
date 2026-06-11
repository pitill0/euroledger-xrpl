from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.payment_intent import PaymentIntentStatus


class PaymentIntentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=12)
    description: str | None = Field(default=None, max_length=255)
    expected_destination: str | None = Field(default=None, max_length=128)
    expires_in_seconds: int = Field(
        default=900,
        ge=60,
        le=86400,
    )


class PaymentIntentConfirm(BaseModel):
    xrpl_transaction_hash: str = Field(..., min_length=64, max_length=128)


class PaymentIntentDetectedPayment(BaseModel):
    reference: str = Field(..., min_length=4, max_length=64)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=12)
    xrpl_transaction_hash: str = Field(..., min_length=64, max_length=128)
    destination: str | None = Field(default=None, max_length=128)
    issuer: str | None = Field(default=None, max_length=128)


class PaymentIntentRead(BaseModel):
    id: str
    reference: str
    amount: Decimal
    currency: str
    status: PaymentIntentStatus
    description: str | None
    expected_destination: str | None
    xrpl_transaction_hash: str | None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
