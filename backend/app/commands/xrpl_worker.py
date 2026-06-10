import argparse
import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.workers.xrpl_scanner import XrplTransactionScanResult, scan_xrpl_transactions
from app.xrpl.account_transactions import fetch_account_transactions
from app.xrpl.client import build_xrpl_client
from app.xrpl.settings import build_xrpl_settings


def build_sample_transactions() -> list[dict[str, Any]]:
    return []


def load_transactions_from_fixture(
    fixture_path: Path,
) -> list[dict[str, Any]]:
    with fixture_path.open(encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)

    if not isinstance(data, list):
        raise ValueError("XRPL fixture must contain a JSON list of transactions.")

    for transaction in data:
        if not isinstance(transaction, dict):
            raise ValueError("XRPL fixture transactions must be JSON objects.")

    return data


def fetch_testnet_transactions(
    limit: int,
) -> list[dict[str, Any]]:
    app_settings = get_settings()
    xrpl_settings = build_xrpl_settings(app_settings)

    if xrpl_settings.merchant_address is None:
        raise ValueError("XRPL_MERCHANT_ADDRESS must be configured to use testnet mode.")

    client = build_xrpl_client(xrpl_settings)

    return fetch_account_transactions(
        client=client,
        account=xrpl_settings.merchant_address,
        limit=limit,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the XRPL payment worker once.",
    )

    source_group = parser.add_mutually_exclusive_group()

    source_group.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Path to a JSON fixture file containing XRPL transactions.",
    )

    source_group.add_argument(
        "--testnet",
        action="store_true",
        help="Fetch transactions from the configured XRPL Testnet account.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of transactions to fetch in testnet mode.",
    )

    return parser.parse_args()


def run_once(
    transactions: list[dict[str, Any]] | None = None,
) -> XrplTransactionScanResult:
    if transactions is None:
        transactions = build_sample_transactions()

    with SessionLocal() as db:
        return scan_xrpl_transactions(
            db=db,
            transactions=transactions,
        )


def print_scan_result(
    result: XrplTransactionScanResult,
) -> None:
    print("XRPL worker scan completed")
    print(f"processed={result.processed}")
    print(f"skipped={result.skipped}")
    print(f"failed={result.failed}")

    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")


def main() -> None:
    args = parse_args()

    transactions: list[dict[str, Any]] | None = None

    if args.fixtures is not None:
        transactions = load_transactions_from_fixture(args.fixtures)
    elif args.testnet:
        transactions = fetch_testnet_transactions(limit=args.limit)

    result = run_once(transactions)
    print_scan_result(result)


if __name__ == "__main__":
    main()
