from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from app.domain.api_keys import (
    generate_api_key,
)
from app.models.merchant import (
    Merchant,
    MerchantApiKey,
)
from app.services.merchant_auth import (
    authenticate_merchant_api_key,
)

PEPPER = "test-pepper-with-at-least-thirty-two-characters"

NOW = datetime(
    2026,
    6,
    12,
    18,
    0,
    tzinfo=UTC,
)


def build_authentication_records(
    *,
    is_active: bool = True,
    revoked_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> tuple[str, Merchant, MerchantApiKey]:
    generated = generate_api_key(
        pepper=PEPPER,
    )

    merchant = Merchant(
        id="merchant-id",
        name="Test Merchant",
        slug="test-merchant",
        is_active=is_active,
        created_at=NOW,
        updated_at=NOW,
    )

    api_key = MerchantApiKey(
        id="key-id",
        merchant_id=merchant.id,
        name="Test key",
        key_prefix=generated.key_prefix,
        key_digest=generated.key_digest,
        revoked_at=revoked_at,
        expires_at=expires_at,
        created_at=NOW,
    )

    api_key.merchant = merchant

    return generated.value, merchant, api_key


def test_authenticate_valid_api_key() -> None:
    db = Mock()

    value, merchant, api_key = build_authentication_records()

    with (
        patch(
            ("app.services.merchant_auth.get_api_key_by_prefix"),
            return_value=api_key,
        ),
        patch(
            ("app.services.merchant_auth.mark_api_key_used"),
        ) as mark_used,
    ):
        result = authenticate_merchant_api_key(
            db=db,
            value=value,
            pepper=PEPPER,
            now=NOW,
        )

    assert result is merchant

    mark_used.assert_called_once_with(
        db,
        api_key,
        used_at=NOW,
    )


def test_reject_revoked_api_key() -> None:
    db = Mock()

    value, _, api_key = build_authentication_records(
        revoked_at=NOW,
    )

    with patch(
        ("app.services.merchant_auth.get_api_key_by_prefix"),
        return_value=api_key,
    ):
        result = authenticate_merchant_api_key(
            db=db,
            value=value,
            pepper=PEPPER,
            now=NOW,
        )

    assert result is None


def test_reject_expired_api_key() -> None:
    db = Mock()

    value, _, api_key = build_authentication_records(
        expires_at=NOW - timedelta(seconds=1),
    )

    with patch(
        ("app.services.merchant_auth.get_api_key_by_prefix"),
        return_value=api_key,
    ):
        result = authenticate_merchant_api_key(
            db=db,
            value=value,
            pepper=PEPPER,
            now=NOW,
        )

    assert result is None


def test_reject_inactive_merchant() -> None:
    db = Mock()

    value, _, api_key = build_authentication_records(
        is_active=False,
    )

    with patch(
        ("app.services.merchant_auth.get_api_key_by_prefix"),
        return_value=api_key,
    ):
        result = authenticate_merchant_api_key(
            db=db,
            value=value,
            pepper=PEPPER,
            now=NOW,
        )

    assert result is None


def test_reject_invalid_key_format() -> None:
    result = authenticate_merchant_api_key(
        db=Mock(),
        value="invalid",
        pepper=PEPPER,
        now=NOW,
    )

    assert result is None
