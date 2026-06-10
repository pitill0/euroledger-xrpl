import argparse
import json
from pathlib import Path
from typing import Any

from app.db.session import SessionLocal
from app.workers.xrpl_scanner import XrplTransactionScanResult, scan_xrpl_transactions


def build_sample_transactions() -> list[dict[str, Any]]:
    return []


def load_transactions_from_fixture(fixture_path: Path) -> list[dict[str, Any]]:
    with fixture_path.open() as fixture_file:
        data = json.load(fixture_file)

    if not isinstance(data, list):
        raise ValueError("XRPL fixture must contain a JSON list of transactions.")

    for transaction in data:
        if not isinstance(transaction, dict):
            raise ValueError("XRPL fixture transactions must be JSON objects.")

    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the XRPL payment worker once.",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Path to a JSON fixture file containing XRPL transactions.",
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


def main() -> None:
    args = parse_args()

    transactions = None
    if args.fixtures is not None:
        transactions = load_transactions_from_fixture(args.fixtures)

    result = run_once(transactions)

    print("XRPL worker scan completed")
    print(f"processed={result.processed}")
    print(f"skipped={result.skipped}")
    print(f"failed={result.failed}")

    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")


if __name__ == "__main__":
    main()
