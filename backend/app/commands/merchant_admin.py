import argparse
from datetime import datetime

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.domain.exceptions import (
    MerchantAlreadyExistsError,
    MerchantNotFoundError,
)
from app.services.merchant_auth import (
    create_merchant,
    issue_merchant_api_key,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Manage EuroLedger merchants and API keys."),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    create_parser = subparsers.add_parser(
        "create",
        help="Create a merchant.",
    )

    create_parser.add_argument(
        "--name",
        required=True,
    )

    create_parser.add_argument(
        "--slug",
        required=True,
    )

    issue_parser = subparsers.add_parser(
        "issue-key",
        help="Issue a new API key.",
    )

    issue_parser.add_argument(
        "--merchant",
        required=True,
        help="Merchant slug.",
    )

    issue_parser.add_argument(
        "--name",
        required=True,
        help="Descriptive key name.",
    )

    issue_parser.add_argument(
        "--expires-at",
        type=datetime.fromisoformat,
        default=None,
        help=("Optional ISO 8601 expiration datetime."),
    )

    return parser


def create_merchant_command(
    *,
    name: str,
    slug: str,
) -> int:
    try:
        with SessionLocal() as db:
            merchant = create_merchant(
                db=db,
                name=name,
                slug=slug,
            )
    except MerchantAlreadyExistsError as exc:
        print(f"error: {exc}")
        return 1

    print("Merchant created")
    print(f"id={merchant.id}")
    print(f"name={merchant.name}")
    print(f"slug={merchant.slug}")

    return 0


def issue_key_command(
    *,
    merchant_slug: str,
    key_name: str,
    expires_at: datetime | None,
) -> int:
    settings = get_settings()

    try:
        with SessionLocal() as db:
            result = issue_merchant_api_key(
                db=db,
                merchant_slug=merchant_slug,
                key_name=key_name,
                pepper=(settings.merchant_api_key_pepper),
                expires_at=expires_at,
            )
    except MerchantNotFoundError as exc:
        print(f"error: {exc}")
        return 1

    print("Merchant API key issued")
    print(f"merchant={merchant_slug}")
    print(f"name={result.api_key.name}")
    print(f"prefix={result.api_key.key_prefix}")
    print()
    print("Store this key securely. It will not be shown again.")
    print(result.value)

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        return create_merchant_command(
            name=args.name,
            slug=args.slug,
        )

    if args.command == "issue-key":
        return issue_key_command(
            merchant_slug=args.merchant,
            key_name=args.name,
            expires_at=args.expires_at,
        )

    parser.error("Unknown command.")

    return 2
