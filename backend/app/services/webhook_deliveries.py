from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.exceptions import WebhookDeliveryRetryConflictError
from app.models.webhook import WebhookDelivery, WebhookDeliveryStatus
from app.repositories.webhook_deliveries import update_webhook_delivery


def utc_now() -> datetime:
    return datetime.now(UTC)


def retry_webhook_delivery(
    db: Session,
    delivery: WebhookDelivery,
    *,
    now: datetime | None = None,
) -> WebhookDelivery:
    if delivery.status == WebhookDeliveryStatus.delivered:
        raise WebhookDeliveryRetryConflictError(
            "Delivered webhook deliveries cannot be retried.",
        )

    retry_at = now or utc_now()

    delivery.status = WebhookDeliveryStatus.pending
    delivery.attempt_count = 0
    delivery.next_attempt_at = retry_at
    delivery.last_attempt_at = None
    delivery.response_status_code = None
    delivery.response_body = None
    delivery.error_message = None

    return update_webhook_delivery(
        db=db,
        delivery=delivery,
    )
