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


def list_webhook_deliveries(
    db: Session,
    *,
    merchant_id: str,
    status: WebhookDeliveryStatus | None,
    event_type: str | None,
    payment_intent_id: str | None,
    endpoint_id: str | None,
    limit: int,
) -> list[WebhookDelivery]:
    statement = select(WebhookDelivery).where(WebhookDelivery.merchant_id == merchant_id)

    if status is not None:
        statement = statement.where(WebhookDelivery.status == status)

    if event_type is not None:
        statement = statement.where(WebhookDelivery.event_type == event_type)

    if payment_intent_id is not None:
        statement = statement.where(WebhookDelivery.payment_intent_id == payment_intent_id)

    if endpoint_id is not None:
        statement = statement.where(WebhookDelivery.endpoint_id == endpoint_id)

    statement = statement.order_by(WebhookDelivery.created_at.desc(), WebhookDelivery.id.desc())
    statement = statement.limit(limit)

    return list(db.execute(statement).scalars().all())


def get_webhook_delivery_by_id(
    db: Session,
    delivery_id: str,
    *,
    merchant_id: str,
) -> WebhookDelivery | None:
    statement = select(WebhookDelivery).where(
        WebhookDelivery.id == delivery_id,
        WebhookDelivery.merchant_id == merchant_id,
    )

    return db.execute(statement).scalar_one_or_none()


def update_webhook_delivery(
    db: Session,
    delivery: WebhookDelivery,
) -> WebhookDelivery:
    db.commit()
    db.refresh(delivery)

    return delivery
