from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.webhook import WebhookDelivery, WebhookDeliveryStatus


def add_webhook_delivery(
    db: Session,
    delivery: WebhookDelivery,
) -> WebhookDelivery:
    db.add(delivery)

    return delivery


def list_due_webhook_deliveries(
    db: Session,
    *,
    now: datetime,
    limit: int,
) -> list[WebhookDelivery]:
    statement = (
        select(WebhookDelivery)
        .options(selectinload(WebhookDelivery.endpoint))
        .where(
            WebhookDelivery.status.in_(
                [
                    WebhookDeliveryStatus.pending,
                    WebhookDeliveryStatus.failed,
                ]
            ),
            or_(
                WebhookDelivery.next_attempt_at.is_(None),
                WebhookDelivery.next_attempt_at <= now,
            ),
        )
        .order_by(WebhookDelivery.next_attempt_at, WebhookDelivery.created_at, WebhookDelivery.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )

    return list(db.execute(statement).scalars().all())
