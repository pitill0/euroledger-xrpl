import argparse
import json
import logging
import signal
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

LOGGER = logging.getLogger(__name__)

SignalHandler = Callable[[int, FrameType | None], None]


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s level=%(levelname)s logger=%(name)s %(message)s"),
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


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


def log_scan_result(
    result: XrplTransactionScanResult,
) -> None:
    LOGGER.info(
        "event=xrpl_scan_completed processed=%d skipped=%d failed=%d",
        result.processed,
        result.skipped,
        result.failed,
    )

    for error in result.errors:
        LOGGER.warning(
            "event=xrpl_scan_error error=%r",
            error,
        )


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

    LOGGER.info(
        (
            "event=xrpl_sync_completed "
            "fetched=%d "
            "processed=%d "
            "skipped=%d "
            "failed=%d "
            "previous_ledger_index=%s "
            "last_ledger_index=%s"
        ),
        result.fetched,
        result.scan_result.processed,
        result.scan_result.skipped,
        result.scan_result.failed,
        result.previous_ledger_index,
        result.last_ledger_index,
    )

    for error in result.scan_result.errors:
        LOGGER.warning(
            "event=xrpl_sync_validation_error error=%r",
            error,
        )


def build_stop_handler(stop_event: Event) -> SignalHandler:
    def handle_stop_signal(
        signum: int,
        frame: FrameType | None,
    ) -> None:
        del frame

        LOGGER.info(
            "event=xrpl_polling_stop_requested signal=%d",
            signum,
        )
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

    LOGGER.info(
        "event=xrpl_polling_started limit=%d poll_interval=%g",
        limit,
        poll_interval,
    )

    try:
        while not worker_stop_event.is_set():
            try:
                run_testnet_once(limit=limit)
            except Exception:
                LOGGER.exception(
                    "event=xrpl_sync_failed",
                )

            if worker_stop_event.wait(poll_interval):
                break
    except KeyboardInterrupt:
        LOGGER.info(
            "event=xrpl_polling_keyboard_interrupt",
        )
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

        LOGGER.info(
            "event=xrpl_polling_stopped",
        )


def main() -> None:
    configure_logging()

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
    log_scan_result(result)


if __name__ == "__main__":
    main()
