import logging
import signal
from argparse import Namespace
from unittest.mock import Mock, call, patch

import pytest

from app.commands.webhook_worker import (
    build_stop_handler,
    main,
    run_once,
    run_polling,
)
from app.services.webhook_delivery import WebhookDeliveryRunResult


def build_result() -> WebhookDeliveryRunResult:
    return WebhookDeliveryRunResult(
        processed=3,
        delivered=1,
        failed=1,
        discarded=1,
        limit=100,
    )


def test_run_once_processes_due_webhook_deliveries() -> None:
    db = Mock()
    expected_result = build_result()

    with (
        patch(
            "app.commands.webhook_worker.SessionLocal",
        ) as session_local,
        patch(
            "app.commands.webhook_worker.process_due_webhook_deliveries",
            return_value=expected_result,
        ) as process_deliveries,
    ):
        session_local.return_value.__enter__.return_value = db

        result = run_once(
            limit=100,
            timeout=5.0,
            max_attempts=5,
        )

    process_deliveries.assert_called_once_with(
        db=db,
        limit=100,
        timeout=5.0,
        max_attempts=5,
    )
    assert result == expected_result


def test_run_once_rolls_back_on_error() -> None:
    db = Mock()

    with (
        patch(
            "app.commands.webhook_worker.SessionLocal",
        ) as session_local,
        patch(
            "app.commands.webhook_worker.process_due_webhook_deliveries",
            side_effect=RuntimeError("database unavailable"),
        ),
        pytest.raises(
            RuntimeError,
            match="database unavailable",
        ),
    ):
        session_local.return_value.__enter__.return_value = db

        run_once(
            limit=100,
            timeout=5.0,
            max_attempts=5,
        )

    db.rollback.assert_called_once_with()


def test_main_runs_one_shot_worker() -> None:
    args = Namespace(
        limit=100,
        timeout=5.0,
        max_attempts=5,
        poll_interval=None,
    )
    result = build_result()

    with (
        patch(
            "app.commands.webhook_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.webhook_worker.run_once",
            return_value=result,
        ) as run_worker,
        patch(
            "app.commands.webhook_worker.log_result",
        ) as log_result,
    ):
        main()

    run_worker.assert_called_once_with(
        limit=100,
        timeout=5.0,
        max_attempts=5,
    )
    log_result.assert_called_once_with(result)


def test_main_runs_polling_mode() -> None:
    args = Namespace(
        limit=100,
        timeout=5.0,
        max_attempts=5,
        poll_interval=60.0,
    )

    with (
        patch(
            "app.commands.webhook_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.webhook_worker.run_polling",
        ) as run_worker_polling,
    ):
        main()

    run_worker_polling.assert_called_once_with(
        limit=100,
        timeout=5.0,
        max_attempts=5,
        poll_interval=60.0,
    )


def test_stop_handler_sets_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop_event = Mock()
    handler = build_stop_handler(stop_event)

    with caplog.at_level(
        logging.INFO,
        logger="app.commands.webhook_worker",
    ):
        handler(
            signal.SIGTERM,
            None,
        )

    stop_event.set.assert_called_once_with()
    assert f"event=webhook_delivery_stop_requested signal={signal.SIGTERM}" in caplog.messages


def test_polling_repeats_without_real_waits() -> None:
    stop_event = Mock()
    stop_event.is_set.side_effect = [
        False,
        False,
    ]
    stop_event.wait.side_effect = [
        False,
        True,
    ]

    result = build_result()

    with (
        patch(
            "app.commands.webhook_worker.signal.signal",
            side_effect=[
                Mock(),
                Mock(),
                None,
                None,
            ],
        ),
        patch(
            "app.commands.webhook_worker.run_once",
            return_value=result,
        ) as run_worker,
        patch(
            "app.commands.webhook_worker.log_result",
        ),
    ):
        run_polling(
            limit=100,
            timeout=5.0,
            max_attempts=5,
            poll_interval=60.0,
            stop_event=stop_event,
        )

    assert run_worker.call_args_list == [
        call(
            limit=100,
            timeout=5.0,
            max_attempts=5,
        ),
        call(
            limit=100,
            timeout=5.0,
            max_attempts=5,
        ),
    ]

    assert stop_event.wait.call_args_list == [
        call(60.0),
        call(60.0),
    ]
