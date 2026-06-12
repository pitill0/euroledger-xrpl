from dataclasses import dataclass
from datetime import UTC, datetime
from secrets import token_hex

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.api_keys import (
    InvalidApiKeyFormatError,
    api_key_digest_matches,
    generate_api_key,
    parse_api_key,
)
from app.domain.exceptions import (
    MerchantAlreadyExistsError,
    MerchantNotFoundError,
)
from app.models.merchant import Merchant, MerchantApiKey
from app.repositories.merchants import (
    get_api_key_by_prefix,
    get_merchant_by_slug,
    mark_api_key_used,
    save_merchant,
    save_merchant_api_key,
)


@dataclass(frozen=True)
class IssuedMerchantApiKey:
    api_key: MerchantApiKey
    value: str


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_merchant_slug(
    value: str,
) -> str:
    return value.strip().lower()


def create_merchant(
    db: Session,
    *,
    name: str,
    slug: str,
) -> Merchant:
    normalized_name = name.strip()
    normalized_slug = normalize_merchant_slug(
        slug,
    )

    if (
        get_merchant_by_slug(
            db,
            normalized_slug,
        )
        is not None
    ):
        raise MerchantAlreadyExistsError(
            f"Merchant slug '{normalized_slug}' already exists.",
        )

    merchant = Merchant(
        name=normalized_name,
        slug=normalized_slug,
    )

    try:
        return save_merchant(
            db,
            merchant,
        )
    except IntegrityError as exc:
        db.rollback()

        raise MerchantAlreadyExistsError(
            f"Merchant slug '{normalized_slug}' already exists.",
        ) from exc


def issue_merchant_api_key(
    db: Session,
    *,
    merchant_slug: str,
    key_name: str,
    pepper: str,
    expires_at: datetime | None = None,
) -> IssuedMerchantApiKey:
    merchant = get_merchant_by_slug(
        db,
        normalize_merchant_slug(
            merchant_slug,
        ),
    )

    if merchant is None:
        raise MerchantNotFoundError(
            f"Merchant '{merchant_slug}' not found.",
        )

    generated = generate_api_key(
        pepper=pepper,
    )

    api_key = MerchantApiKey(
        merchant_id=merchant.id,
        name=key_name.strip(),
        key_prefix=generated.key_prefix,
        key_digest=generated.key_digest,
        expires_at=expires_at,
    )

    try:
        persisted_api_key = save_merchant_api_key(
            db,
            api_key,
        )
    except IntegrityError:
        db.rollback()

        generated = generate_api_key(
            pepper=pepper,
        )

        api_key.id = token_hex(18)
        api_key.key_prefix = generated.key_prefix
        api_key.key_digest = generated.key_digest

        persisted_api_key = save_merchant_api_key(
            db,
            api_key,
        )

    return IssuedMerchantApiKey(
        api_key=persisted_api_key,
        value=generated.value,
    )


def authenticate_merchant_api_key(
    db: Session,
    *,
    value: str,
    pepper: str,
    now: datetime | None = None,
) -> Merchant | None:
    authenticated_at = now or utc_now()

    try:
        parsed = parse_api_key(value)
    except InvalidApiKeyFormatError:
        return None

    api_key = get_api_key_by_prefix(
        db,
        parsed.key_prefix,
    )

    if api_key is None:
        return None

    if api_key.revoked_at is not None:
        return None

    if api_key.expires_at is not None and api_key.expires_at <= authenticated_at:
        return None

    if not api_key.merchant.is_active:
        return None

    if not api_key_digest_matches(
        parsed.value,
        expected_digest=api_key.key_digest,
        pepper=pepper,
    ):
        return None

    mark_api_key_used(
        db,
        api_key,
        used_at=authenticated_at,
    )

    return api_key.merchant
