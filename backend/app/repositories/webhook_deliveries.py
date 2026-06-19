from sqlalchemy.orm import Session

from app.models.webhook import WebhookDelivery


def add_webhook_delivery(
    db: Session,
    delivery: WebhookDelivery,
) -> WebhookDelivery:
    db.add(delivery)

    return delivery
