from typing import Annotated

from fastapi import APIRouter, Depends, Response
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.payment_intent_expiration_metrics import (
    generate_payment_intent_expiration_metrics,
)
from app.services.worker_metrics import generate_xrpl_worker_metrics

router = APIRouter(tags=["metrics"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/metrics",
    include_in_schema=False,
)
def metrics_endpoint(
    db: DbSession,
) -> Response:
    settings = get_settings()

    xrpl_metrics = generate_xrpl_worker_metrics(
        db=db,
        stale_after_seconds=settings.xrpl_worker_stale_after_seconds,
    )

    expiration_metrics = generate_payment_intent_expiration_metrics(
        db=db,
        stale_after_seconds=(settings.payment_intent_expirer_stale_after_seconds),
    )

    return Response(
        content=xrpl_metrics + expiration_metrics,
        media_type=CONTENT_TYPE_LATEST,
    )
