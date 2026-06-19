from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentMerchant
from app.db.session import get_db
from app.models.webhook import WebhookDeliveryStatus
from app.repositories.webhook_deliveries import (
    get_webhook_delivery_by_id,
    list_webhook_deliveries,
)
from app.schemas.webhook import (
    WebhookDeliveryListResponse,
    WebhookDeliveryRead,
)

router = APIRouter(
    prefix="/webhook-deliveries",
    tags=["webhook-deliveries"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]

StatusFilter = Annotated[
    WebhookDeliveryStatus | None,
    Query(),
]

EventTypeFilter = Annotated[
    str | None,
    Query(
        min_length=1,
        max_length=100,
    ),
]

PaymentIntentFilter = Annotated[
    str | None,
    Query(
        min_length=1,
        max_length=36,
    ),
]

EndpointFilter = Annotated[
    str | None,
    Query(
        min_length=1,
        max_length=36,
    ),
]

LimitFilter = Annotated[
    int,
    Query(
        ge=1,
        le=100,
    ),
]


@router.get(
    "",
    response_model=WebhookDeliveryListResponse,
)
def list_webhook_deliveries_endpoint(
    db: DbSession,
    merchant: CurrentMerchant,
    status_filter: StatusFilter = None,
    event_type: EventTypeFilter = None,
    payment_intent_id: PaymentIntentFilter = None,
    endpoint_id: EndpointFilter = None,
    limit: LimitFilter = 20,
) -> WebhookDeliveryListResponse:
    deliveries = list_webhook_deliveries(
        db=db,
        merchant_id=merchant.id,
        status=status_filter,
        event_type=event_type,
        payment_intent_id=payment_intent_id,
        endpoint_id=endpoint_id,
        limit=limit,
    )

    return WebhookDeliveryListResponse(
        items=[WebhookDeliveryRead.model_validate(delivery) for delivery in deliveries],
    )


@router.get(
    "/{delivery_id}",
    response_model=WebhookDeliveryRead,
)
def get_webhook_delivery_endpoint(
    delivery_id: str,
    db: DbSession,
    merchant: CurrentMerchant,
) -> WebhookDeliveryRead:
    delivery = get_webhook_delivery_by_id(
        db=db,
        delivery_id=delivery_id,
        merchant_id=merchant.id,
    )

    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook delivery not found",
        )

    return delivery
