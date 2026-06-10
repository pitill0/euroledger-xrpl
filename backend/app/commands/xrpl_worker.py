from typing import Any

from app.db.session import SessionLocal
from app.workers.xrpl_scanner import XrplTransactionScanResult, scan_xrpl_transactions


def build_sample_transactions() -> list[dict[str, Any]]:
    return []


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
    result = run_once()

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
