import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass

API_KEY_PREFIX = "elk"
API_KEY_PUBLIC_PREFIX_LENGTH = 12
API_KEY_SECRET_BYTES = 32

API_KEY_PATTERN = re.compile(r"^elk_([a-f0-9]{12})_([A-Za-z0-9_-]{32,})$")


class InvalidApiKeyFormatError(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedApiKey:
    value: str
    key_prefix: str
    key_digest: str


@dataclass(frozen=True)
class ParsedApiKey:
    value: str
    key_prefix: str


def calculate_api_key_digest(
    api_key: str,
    *,
    pepper: str,
) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        api_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_api_key(
    *,
    pepper: str,
) -> GeneratedApiKey:
    public_prefix = secrets.token_hex(
        API_KEY_PUBLIC_PREFIX_LENGTH // 2,
    )

    secret = secrets.token_urlsafe(
        API_KEY_SECRET_BYTES,
    )

    value = f"{API_KEY_PREFIX}_{public_prefix}_{secret}"

    return GeneratedApiKey(
        value=value,
        key_prefix=public_prefix,
        key_digest=calculate_api_key_digest(
            value,
            pepper=pepper,
        ),
    )


def parse_api_key(
    value: str,
) -> ParsedApiKey:
    match = API_KEY_PATTERN.fullmatch(value)

    if match is None:
        raise InvalidApiKeyFormatError(
            "Invalid API key format.",
        )

    return ParsedApiKey(
        value=value,
        key_prefix=match.group(1),
    )


def api_key_digest_matches(
    api_key: str,
    *,
    expected_digest: str,
    pepper: str,
) -> bool:
    calculated_digest = calculate_api_key_digest(
        api_key,
        pepper=pepper,
    )

    return hmac.compare_digest(
        calculated_digest,
        expected_digest,
    )
