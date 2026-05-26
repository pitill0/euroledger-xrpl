from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.payment_intent import PaymentIntentStatus


class PaymentIntentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=12)
    description: str | None = Field(default=None, max_length=255)


class PaymentIntentRead(BaseModel):
    id: str
    reference: str
    amount: Decimal
    currency: str
    status: PaymentIntentStatus
    description: str | None
    xrpl_transaction_hash: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
