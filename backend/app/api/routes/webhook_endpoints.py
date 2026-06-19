from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentMerchant
from app.db.session import get_db
from app.repositories.webhook_endpoints import (
    create_webhook_endpoint,
    delete_webhook_endpoint,
    get_webhook_endpoint_by_id,
    list_webhook_endpoints,
    update_webhook_endpoint,
)
from app.schemas.webhook import (
    WebhookEndpointCreate,
    WebhookEndpointListResponse,
    WebhookEndpointRead,
    WebhookEndpointUpdate,
)

router = APIRouter(
    prefix="/webhook-endpoints",
    tags=["webhook-endpoints"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "",
    response_model=WebhookEndpointRead,
    status_code=status.HTTP_201_CREATED,
)
def create_webhook_endpoint_endpoint(
    payload: WebhookEndpointCreate,
    db: DbSession,
    merchant: CurrentMerchant,
) -> WebhookEndpointRead:
    return create_webhook_endpoint(
        db=db,
        merchant_id=merchant.id,
        url=payload.url,
        secret=payload.secret,
        enabled=payload.enabled,
    )


@router.get(
    "",
    response_model=WebhookEndpointListResponse,
)
def list_webhook_endpoints_endpoint(
    db: DbSession,
    merchant: CurrentMerchant,
) -> WebhookEndpointListResponse:
    endpoints = list_webhook_endpoints(
        db=db,
        merchant_id=merchant.id,
    )

    return WebhookEndpointListResponse(
        items=[WebhookEndpointRead.model_validate(endpoint) for endpoint in endpoints],
    )


@router.get(
    "/{endpoint_id}",
    response_model=WebhookEndpointRead,
)
def get_webhook_endpoint_endpoint(
    endpoint_id: str,
    db: DbSession,
    merchant: CurrentMerchant,
) -> WebhookEndpointRead:
    endpoint = get_webhook_endpoint_by_id(
        db=db,
        endpoint_id=endpoint_id,
        merchant_id=merchant.id,
    )

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found",
        )

    return endpoint


@router.patch(
    "/{endpoint_id}",
    response_model=WebhookEndpointRead,
)
def update_webhook_endpoint_endpoint(
    endpoint_id: str,
    payload: WebhookEndpointUpdate,
    db: DbSession,
    merchant: CurrentMerchant,
) -> WebhookEndpointRead:
    endpoint = get_webhook_endpoint_by_id(
        db=db,
        endpoint_id=endpoint_id,
        merchant_id=merchant.id,
    )

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    for field_name, value in update_data.items():
        setattr(
            endpoint,
            field_name,
            value,
        )

    return update_webhook_endpoint(
        db=db,
        endpoint=endpoint,
    )


@router.delete(
    "/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_webhook_endpoint_endpoint(
    endpoint_id: str,
    db: DbSession,
    merchant: CurrentMerchant,
) -> Response:
    endpoint = get_webhook_endpoint_by_id(
        db=db,
        endpoint_id=endpoint_id,
        merchant_id=merchant.id,
    )

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found",
        )

    delete_webhook_endpoint(
        db=db,
        endpoint=endpoint,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
