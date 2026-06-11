import logging
import signal
from argparse import Namespace
from unittest.mock import Mock, call, patch

import pytest

from app.commands.xrpl_worker import (
    build_stop_handler,
    main,
    parse_args,
    positive_poll_interval,
    run_testnet_polling,
)


def test_positive_poll_interval_accepts_positive_value() -> None:
    assert positive_poll_interval("30") == 30.0
    assert positive_poll_interval("0.5") == 0.5


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
    ],
)
def test_positive_poll_interval_rejects_non_positive_value(
    value: str,
) -> None:
    with pytest.raises(
        Exception,
        match="greater than zero",
    ):
        positive_poll_interval(value)


def test_parse_args_accepts_testnet_polling() -> None:
    with patch(
        "sys.argv",
        [
            "xrpl-worker",
            "--testnet",
            "--limit",
            "5",
            "--poll-interval",
            "30",
        ],
    ):
        args = parse_args()

    assert args == Namespace(
        fixtures=None,
        testnet=True,
        limit=5,
        poll_interval=30.0,
    )


def test_parse_args_rejects_polling_without_testnet(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch(
            "sys.argv",
            [
                "xrpl-worker",
                "--poll-interval",
                "30",
            ],
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        parse_args()

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "--poll-interval requires --testnet" in captured.err


def test_main_runs_testnet_polling() -> None:
    args = Namespace(
        fixtures=None,
        testnet=True,
        limit=5,
        poll_interval=30.0,
    )

    with (
        patch(
            "app.commands.xrpl_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.xrpl_worker.run_testnet_polling",
        ) as run_polling,
    ):
        main()

    run_polling.assert_called_once_with(
        limit=5,
        poll_interval=30.0,
    )


def test_main_keeps_testnet_one_shot_mode() -> None:
    args = Namespace(
        fixtures=None,
        testnet=True,
        limit=5,
        poll_interval=None,
    )

    with (
        patch(
            "app.commands.xrpl_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.xrpl_worker.run_testnet_once",
        ) as run_once,
        patch(
            "app.commands.xrpl_worker.run_testnet_polling",
        ) as run_polling,
    ):
        main()

    run_once.assert_called_once_with(limit=5)
    run_polling.assert_not_called()


def test_stop_handler_sets_stop_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop_event = Mock()

    handler = build_stop_handler(stop_event)

    with caplog.at_level(
        logging.INFO,
        logger="app.commands.xrpl_worker",
    ):
        handler(signal.SIGTERM, None)

    stop_event.set.assert_called_once_with()

    assert f"event=xrpl_polling_stop_requested signal={signal.SIGTERM}" in caplog.messages


def test_run_testnet_polling_repeats_until_stop_event_is_set(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop_event = Mock()
    stop_event.is_set.side_effect = [
        False,
        False,
    ]
    stop_event.wait.side_effect = [
        False,
        True,
    ]

    previous_sigint_handler = Mock()
    previous_sigterm_handler = Mock()

    with (
        patch(
            "app.commands.xrpl_worker.signal.signal",
            side_effect=[
                previous_sigint_handler,
                previous_sigterm_handler,
                None,
                None,
            ],
        ) as register_signal,
        patch(
            "app.commands.xrpl_worker.run_testnet_once",
        ) as run_once,
        caplog.at_level(
            logging.INFO,
            logger="app.commands.xrpl_worker",
        ),
    ):
        run_testnet_polling(
            limit=5,
            poll_interval=30.0,
            stop_event=stop_event,
        )

    assert run_once.call_count == 2
    assert run_once.call_args_list == [
        call(limit=5),
        call(limit=5),
    ]

    assert stop_event.wait.call_args_list == [
        call(30.0),
        call(30.0),
    ]

    assert register_signal.call_count == 4
    register_signal.assert_any_call(
        signal.SIGINT,
        previous_sigint_handler,
    )
    register_signal.assert_any_call(
        signal.SIGTERM,
        previous_sigterm_handler,
    )

    assert "event=xrpl_polling_started limit=5 poll_interval=30" in caplog.messages
    assert "event=xrpl_polling_stopped" in caplog.messages


def test_run_testnet_polling_continues_after_cycle_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop_event = Mock()
    stop_event.is_set.side_effect = [
        False,
        False,
    ]
    stop_event.wait.side_effect = [
        False,
        True,
    ]

    with (
        patch(
            "app.commands.xrpl_worker.signal.signal",
            side_effect=[
                Mock(),
                Mock(),
                None,
                None,
            ],
        ),
        patch(
            "app.commands.xrpl_worker.run_testnet_once",
            side_effect=[
                RuntimeError("temporary XRPL failure"),
                None,
            ],
        ) as run_once,
        caplog.at_level(
            logging.ERROR,
            logger="app.commands.xrpl_worker",
        ),
    ):
        run_testnet_polling(
            limit=5,
            poll_interval=30.0,
            stop_event=stop_event,
        )

    assert run_once.call_count == 2
    assert "event=xrpl_sync_failed" in caplog.messages

    error_record = next(
        record for record in caplog.records if record.getMessage() == "event=xrpl_sync_failed"
    )

    assert error_record.levelno == logging.ERROR
    assert error_record.exc_info is not None


def test_run_testnet_polling_handles_keyboard_interrupt(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop_event = Mock()
    stop_event.is_set.return_value = False

    with (
        patch(
            "app.commands.xrpl_worker.signal.signal",
            side_effect=[
                Mock(),
                Mock(),
                None,
                None,
            ],
        ),
        patch(
            "app.commands.xrpl_worker.run_testnet_once",
            side_effect=KeyboardInterrupt,
        ),
        caplog.at_level(
            logging.INFO,
            logger="app.commands.xrpl_worker",
        ),
    ):
        run_testnet_polling(
            limit=5,
            poll_interval=30.0,
            stop_event=stop_event,
        )

    stop_event.set.assert_called_once_with()
    stop_event.wait.assert_not_called()

    assert "event=xrpl_polling_keyboard_interrupt" in caplog.messages
    assert "event=xrpl_polling_stopped" in caplog.messages
