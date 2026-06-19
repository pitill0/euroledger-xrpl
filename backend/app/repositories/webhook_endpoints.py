from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.webhook import MerchantWebhookEndpoint


def create_webhook_endpoint(
    db: Session,
    *,
    merchant_id: str,
    url: str,
    secret: str,
    enabled: bool,
) -> MerchantWebhookEndpoint:
    endpoint = MerchantWebhookEndpoint(
        merchant_id=merchant_id,
        url=url,
        secret=secret,
        enabled=enabled,
    )

    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)

    return endpoint


def list_webhook_endpoints(
    db: Session,
    *,
    merchant_id: str,
) -> list[MerchantWebhookEndpoint]:
    statement = (
        select(MerchantWebhookEndpoint)
        .where(MerchantWebhookEndpoint.merchant_id == merchant_id)
        .order_by(MerchantWebhookEndpoint.created_at.desc(), MerchantWebhookEndpoint.id.desc())
    )

    return list(db.execute(statement).scalars().all())


def list_enabled_webhook_endpoints(
    db: Session,
    *,
    merchant_id: str,
) -> list[MerchantWebhookEndpoint]:
    statement = (
        select(MerchantWebhookEndpoint)
        .where(
            MerchantWebhookEndpoint.merchant_id == merchant_id,
            MerchantWebhookEndpoint.enabled.is_(True),
        )
        .order_by(MerchantWebhookEndpoint.created_at, MerchantWebhookEndpoint.id)
    )

    return list(db.execute(statement).scalars().all())


def get_webhook_endpoint_by_id(
    db: Session,
    endpoint_id: str,
    *,
    merchant_id: str,
) -> MerchantWebhookEndpoint | None:
    statement = select(MerchantWebhookEndpoint).where(
        MerchantWebhookEndpoint.id == endpoint_id,
        MerchantWebhookEndpoint.merchant_id == merchant_id,
    )

    return db.execute(statement).scalar_one_or_none()


def update_webhook_endpoint(
    db: Session,
    endpoint: MerchantWebhookEndpoint,
) -> MerchantWebhookEndpoint:
    db.commit()
    db.refresh(endpoint)

    return endpoint


def delete_webhook_endpoint(
    db: Session,
    endpoint: MerchantWebhookEndpoint,
) -> None:
    db.delete(endpoint)
    db.commit()
