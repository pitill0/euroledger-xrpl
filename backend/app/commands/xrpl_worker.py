import argparse
import json
import signal
import sys
from collections.abc import Callable
from pathlib import Path
from threading import Event
from types import FrameType
from typing import Any

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.workers.xrpl_scanner import XrplTransactionScanResult, scan_xrpl_transactions
from app.workers.xrpl_sync import synchronize_xrpl_account_transactions
from app.xrpl.account_transactions import fetch_account_transactions
from app.xrpl.client import build_xrpl_client
from app.xrpl.settings import build_xrpl_settings

SignalHandler = Callable[[int, FrameType | None], None]


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


def positive_poll_interval(value: str) -> float:
    interval = float(value)

    if interval <= 0:
        raise argparse.ArgumentTypeError(
            "poll interval must be greater than zero",
        )

    return interval


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the XRPL payment worker.",
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
        help="Maximum number of transactions to fetch per Testnet request.",
    )

    parser.add_argument(
        "--poll-interval",
        type=positive_poll_interval,
        default=None,
        metavar="SECONDS",
        help="Repeat Testnet synchronization every SECONDS instead of running once.",
    )

    args = parser.parse_args()

    if args.poll_interval is not None and not args.testnet:
        parser.error("--poll-interval requires --testnet")

    return args


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


def run_testnet_once(
    limit: int,
) -> None:
    app_settings = get_settings()
    xrpl_settings = build_xrpl_settings(app_settings)

    if xrpl_settings.merchant_address is None:
        raise ValueError("XRPL_MERCHANT_ADDRESS must be configured to use testnet mode.")

    client = build_xrpl_client(xrpl_settings)

    with SessionLocal() as db:
        result = synchronize_xrpl_account_transactions(
            db=db,
            client=client,
            account=xrpl_settings.merchant_address,
            limit=limit,
        )

    print("XRPL worker synchronization completed")
    print(f"fetched={result.fetched}")
    print(f"processed={result.scan_result.processed}")
    print(f"skipped={result.scan_result.skipped}")
    print(f"failed={result.scan_result.failed}")
    print(f"previous_ledger_index={result.previous_ledger_index}")
    print(f"last_ledger_index={result.last_ledger_index}")

    if result.scan_result.errors:
        print("errors:")
        for error in result.scan_result.errors:
            print(f"- {error}")


def build_stop_handler(stop_event: Event) -> SignalHandler:
    def handle_stop_signal(
        signum: int,
        frame: FrameType | None,
    ) -> None:
        del signum, frame
        stop_event.set()

    return handle_stop_signal


def run_testnet_polling(
    *,
    limit: int,
    poll_interval: float,
    stop_event: Event | None = None,
) -> None:
    worker_stop_event = stop_event or Event()
    stop_handler = build_stop_handler(worker_stop_event)

    previous_sigint_handler = signal.signal(
        signal.SIGINT,
        stop_handler,
    )
    previous_sigterm_handler = signal.signal(
        signal.SIGTERM,
        stop_handler,
    )

    print(f"XRPL worker polling started interval={poll_interval:g}s")

    try:
        while not worker_stop_event.is_set():
            try:
                run_testnet_once(limit=limit)
            except Exception as exc:
                print(
                    f"XRPL worker synchronization failed: {exc}",
                    file=sys.stderr,
                )

            if worker_stop_event.wait(poll_interval):
                break
    except KeyboardInterrupt:
        worker_stop_event.set()
    finally:
        signal.signal(
            signal.SIGINT,
            previous_sigint_handler,
        )
        signal.signal(
            signal.SIGTERM,
            previous_sigterm_handler,
        )

        print("XRPL worker polling stopped")


def main() -> None:
    args = parse_args()
    poll_interval = getattr(args, "poll_interval", None)

    if args.testnet:
        if poll_interval is not None:
            run_testnet_polling(
                limit=args.limit,
                poll_interval=poll_interval,
            )
            return

        run_testnet_once(limit=args.limit)
        return

    transactions: list[dict[str, Any]] | None = None

    if args.fixtures is not None:
        transactions = load_transactions_from_fixture(args.fixtures)

    result = run_once(transactions)
    print_scan_result(result)


if __name__ == "__main__":
    main()
