import logging
import signal
from argparse import Namespace
from unittest.mock import Mock, call, patch

import pytest

from app.commands.payment_intent_expirer import (
    build_stop_handler,
    main,
    run_once,
    run_polling,
)
from app.services.payment_intents import (
    PaymentIntentExpirationResult,
)


def test_run_once_expires_payment_intents() -> None:
    db = Mock()

    expected_result = PaymentIntentExpirationResult(
        expired=3,
        limit=100,
    )

    with (
        patch(
            "app.commands.payment_intent_expirer.SessionLocal",
        ) as session_local,
        patch(
            ("app.commands.payment_intent_expirer.expire_pending_payment_intents"),
            return_value=expected_result,
        ) as expire_payment_intents,
    ):
        session_local.return_value.__enter__.return_value = db

        result = run_once(
            limit=100,
        )

    expire_payment_intents.assert_called_once_with(
        db=db,
        limit=100,
    )

    assert result == expected_result


def test_main_runs_one_shot_expiration() -> None:
    args = Namespace(
        limit=100,
        poll_interval=None,
    )

    result = PaymentIntentExpirationResult(
        expired=3,
        limit=100,
    )

    with (
        patch(
            "app.commands.payment_intent_expirer.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.payment_intent_expirer.run_once",
            return_value=result,
        ) as run_expiration,
        patch(
            "app.commands.payment_intent_expirer.log_result",
        ) as log_result,
    ):
        main()

    run_expiration.assert_called_once_with(
        limit=100,
    )
    log_result.assert_called_once_with(result)


def test_main_runs_polling_mode() -> None:
    args = Namespace(
        limit=100,
        poll_interval=60.0,
    )

    with (
        patch(
            "app.commands.payment_intent_expirer.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.payment_intent_expirer.run_polling",
        ) as run_expiration_polling,
    ):
        main()

    run_expiration_polling.assert_called_once_with(
        limit=100,
        poll_interval=60.0,
    )


def test_stop_handler_sets_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop_event = Mock()
    handler = build_stop_handler(stop_event)

    with caplog.at_level(
        logging.INFO,
        logger="app.commands.payment_intent_expirer",
    ):
        handler(
            signal.SIGTERM,
            None,
        )

    stop_event.set.assert_called_once_with()

    assert (
        f"event=payment_intent_expiration_stop_requested signal={signal.SIGTERM}"
    ) in caplog.messages


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

    result = PaymentIntentExpirationResult(
        expired=1,
        limit=100,
    )

    with (
        patch(
            "app.commands.payment_intent_expirer.signal.signal",
            side_effect=[
                Mock(),
                Mock(),
                None,
                None,
            ],
        ),
        patch(
            "app.commands.payment_intent_expirer.run_once",
            return_value=result,
        ) as run_expiration,
        patch(
            "app.commands.payment_intent_expirer.log_result",
        ),
    ):
        run_polling(
            limit=100,
            poll_interval=60.0,
            stop_event=stop_event,
        )

    assert run_expiration.call_args_list == [
        call(limit=100),
        call(limit=100),
    ]

    assert stop_event.wait.call_args_list == [
        call(60.0),
        call(60.0),
    ]


def test_polling_continues_after_cycle_error(
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

    result = PaymentIntentExpirationResult(
        expired=0,
        limit=100,
    )

    with (
        patch(
            "app.commands.payment_intent_expirer.signal.signal",
            side_effect=[
                Mock(),
                Mock(),
                None,
                None,
            ],
        ),
        patch(
            "app.commands.payment_intent_expirer.run_once",
            side_effect=[
                RuntimeError("database unavailable"),
                result,
            ],
        ) as run_expiration,
        patch(
            "app.commands.payment_intent_expirer.log_result",
        ),
        caplog.at_level(
            logging.ERROR,
            logger="app.commands.payment_intent_expirer",
        ),
    ):
        run_polling(
            limit=100,
            poll_interval=60.0,
            stop_event=stop_event,
        )

    assert run_expiration.call_count == 2
    assert "event=payment_intent_expiration_failed" in caplog.messages
