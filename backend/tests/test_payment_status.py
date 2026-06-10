from app.domain.payment_status import (
    can_transition_payment_intent_status,
    is_terminal_payment_intent_status,
)
from app.models.payment_intent import PaymentIntentStatus


def test_pending_payment_intent_can_be_confirmed() -> None:
    assert can_transition_payment_intent_status(
        PaymentIntentStatus.pending,
        PaymentIntentStatus.confirmed,
    )


def test_pending_payment_intent_can_be_expired() -> None:
    assert can_transition_payment_intent_status(
        PaymentIntentStatus.pending,
        PaymentIntentStatus.expired,
    )


def test_pending_payment_intent_can_be_cancelled() -> None:
    assert can_transition_payment_intent_status(
        PaymentIntentStatus.pending,
        PaymentIntentStatus.cancelled,
    )


def test_confirmed_payment_intent_is_terminal() -> None:
    assert is_terminal_payment_intent_status(PaymentIntentStatus.confirmed)


def test_expired_payment_intent_is_terminal() -> None:
    assert is_terminal_payment_intent_status(PaymentIntentStatus.expired)


def test_cancelled_payment_intent_is_terminal() -> None:
    assert is_terminal_payment_intent_status(PaymentIntentStatus.cancelled)


def test_confirmed_payment_intent_cannot_be_cancelled() -> None:
    assert not can_transition_payment_intent_status(
        PaymentIntentStatus.confirmed,
        PaymentIntentStatus.cancelled,
    )


def test_expired_payment_intent_cannot_be_confirmed() -> None:
    assert not can_transition_payment_intent_status(
        PaymentIntentStatus.expired,
        PaymentIntentStatus.confirmed,
    )


def test_cancelled_payment_intent_cannot_be_confirmed() -> None:
    assert not can_transition_payment_intent_status(
        PaymentIntentStatus.cancelled,
        PaymentIntentStatus.confirmed,
    )
