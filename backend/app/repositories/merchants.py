from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.merchant import Merchant, MerchantApiKey


def get_merchant_by_id(
    db: Session,
    merchant_id: str,
) -> Merchant | None:
    return db.get(
        Merchant,
        merchant_id,
    )


def get_merchant_by_slug(
    db: Session,
    slug: str,
) -> Merchant | None:
    statement = select(Merchant).where(
        Merchant.slug == slug,
    )

    return db.execute(
        statement,
    ).scalar_one_or_none()


def get_api_key_by_prefix(
    db: Session,
    key_prefix: str,
) -> MerchantApiKey | None:
    statement = (
        select(MerchantApiKey)
        .options(
            joinedload(
                MerchantApiKey.merchant,
            )
        )
        .where(
            MerchantApiKey.key_prefix == key_prefix,
        )
    )

    return db.execute(
        statement,
    ).scalar_one_or_none()


def save_merchant(
    db: Session,
    merchant: Merchant,
) -> Merchant:
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    return merchant


def save_merchant_api_key(
    db: Session,
    api_key: MerchantApiKey,
) -> MerchantApiKey:
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key


def mark_api_key_used(
    db: Session,
    api_key: MerchantApiKey,
    *,
    used_at: datetime,
) -> None:
    api_key.last_used_at = used_at
    db.commit()
