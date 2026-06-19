import argparse
import logging
import signal
from collections.abc import Callable
from threading import Event
from types import FrameType

from app.db.session import SessionLocal
from app.repositories.webhook_delivery_worker_states import (
    get_or_create_webhook_delivery_worker_state,
    mark_webhook_delivery_cycle_failed,
    mark_webhook_delivery_cycle_started,
    mark_webhook_delivery_cycle_succeeded,
)
from app.services.webhook_delivery import (
    DEFAULT_WEBHOOK_MAX_ATTEMPTS,
    DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
    WebhookDeliveryRunResult,
    process_due_webhook_deliveries,
)

LOGGER = logging.getLogger(__name__)

SignalHandler = Callable[[int, FrameType | None], None]


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s level=%(levelname)s logger=%(name)s %(message)s"),
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


def positive_integer(value: str) -> int:
    parsed_value = int(value)

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero",
        )

    return parsed_value


def positive_float(value: str) -> float:
    parsed_value = float(value)

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero",
        )

    return parsed_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deliver pending EuroLedger merchant webhooks.",
    )

    parser.add_argument(
        "--limit",
        type=positive_integer,
        default=100,
        help="Maximum number of webhook deliveries to process per cycle.",
    )

    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help="HTTP timeout per webhook delivery.",
    )

    parser.add_argument(
        "--max-attempts",
        type=positive_integer,
        default=DEFAULT_WEBHOOK_MAX_ATTEMPTS,
        help="Discard deliveries after this many attempts.",
    )

    parser.add_argument(
        "--poll-interval",
        type=positive_float,
        default=None,
        metavar="SECONDS",
        help="Repeat delivery processing every SECONDS instead of running once.",
    )

    return parser.parse_args()


def run_once(
    *,
    limit: int,
    timeout: float,
    max_attempts: int,
) -> WebhookDeliveryRunResult:
    with SessionLocal() as db:
        state = get_or_create_webhook_delivery_worker_state(db)

        mark_webhook_delivery_cycle_started(
            db=db,
            state=state,
        )

        try:
            result = process_due_webhook_deliveries(
                db=db,
                limit=limit,
                timeout=timeout,
                max_attempts=max_attempts,
            )
        except Exception as exc:
            db.rollback()

            state = get_or_create_webhook_delivery_worker_state(db)

            mark_webhook_delivery_cycle_failed(
                db=db,
                state=state,
                error=str(exc),
            )

            raise

        mark_webhook_delivery_cycle_succeeded(
            db=db,
            state=state,
            processed=result.processed,
            delivered=result.delivered,
            failed=result.failed,
            discarded=result.discarded,
        )

        return result


def log_result(
    result: WebhookDeliveryRunResult,
) -> None:
    LOGGER.info(
        (
            "event=webhook_delivery_completed processed=%d delivered=%d "
            "failed=%d discarded=%d limit=%d"
        ),
        result.processed,
        result.delivered,
        result.failed,
        result.discarded,
        result.limit,
    )


def build_stop_handler(
    stop_event: Event,
) -> SignalHandler:
    def handle_stop_signal(
        signum: int,
        frame: FrameType | None,
    ) -> None:
        del frame

        LOGGER.info(
            "event=webhook_delivery_stop_requested signal=%d",
            signum,
        )

        stop_event.set()

    return handle_stop_signal


def run_polling(
    *,
    limit: int,
    timeout: float,
    max_attempts: int,
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
        (
            "event=webhook_delivery_polling_started limit=%d timeout=%g "
            "max_attempts=%d poll_interval=%g"
        ),
        limit,
        timeout,
        max_attempts,
        poll_interval,
    )

    try:
        while not worker_stop_event.is_set():
            try:
                result = run_once(
                    limit=limit,
                    timeout=timeout,
                    max_attempts=max_attempts,
                )
                log_result(result)
            except Exception:
                LOGGER.exception(
                    "event=webhook_delivery_failed",
                )

            if worker_stop_event.wait(poll_interval):
                break
    except KeyboardInterrupt:
        LOGGER.info(
            "event=webhook_delivery_keyboard_interrupt",
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
            "event=webhook_delivery_polling_stopped",
        )


def main() -> None:
    configure_logging()
    args = parse_args()

    if args.poll_interval is not None:
        run_polling(
            limit=args.limit,
            timeout=args.timeout,
            max_attempts=args.max_attempts,
            poll_interval=args.poll_interval,
        )
        return

    result = run_once(
        limit=args.limit,
        timeout=args.timeout,
        max_attempts=args.max_attempts,
    )
    log_result(result)


if __name__ == "__main__":
    main()
