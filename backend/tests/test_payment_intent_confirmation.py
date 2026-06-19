from unittest.mock import Mock, patch

import pytest

from app.domain.exceptions import InvalidPaymentIntentStatusTransitionError
from app.models.payment_intent import PaymentIntent, PaymentIntentStatus
from app.services.payment_intents import confirm_payment_intent
from app.services.webhook_events import PAYMENT_INTENT_CONFIRMED_EVENT

XRPL_TRANSACTION_HASH = "A" * 64


def test_confirm_pending_payment_intent() -> None:
    db = Mock()
    payment_intent = PaymentIntent(
        merchant_id="merchant-id",
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=PaymentIntentStatus.pending,
    )

    with patch(
        "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
    ) as enqueue_deliveries:
        confirmed_payment_intent = confirm_payment_intent(
            db=db,
            payment_intent=payment_intent,
            xrpl_transaction_hash=XRPL_TRANSACTION_HASH,
        )

    assert confirmed_payment_intent.status == PaymentIntentStatus.confirmed
    assert confirmed_payment_intent.xrpl_transaction_hash == XRPL_TRANSACTION_HASH
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(payment_intent)

    enqueue_deliveries.assert_called_once_with(
        db=db,
        payment_intent=payment_intent,
        event_type=PAYMENT_INTENT_CONFIRMED_EVENT,
    )


@pytest.mark.parametrize(
    "status",
    [
        PaymentIntentStatus.confirmed,
        PaymentIntentStatus.expired,
        PaymentIntentStatus.cancelled,
    ],
)
def test_cannot_confirm_non_pending_payment_intent(
    status: PaymentIntentStatus,
) -> None:
    db = Mock()
    payment_intent = PaymentIntent(
        merchant_id="merchant-id",
        reference="EL-TESTREFERENCE",
        amount="25.00",
        currency="EUR",
        status=status,
    )

    with patch(
        "app.services.payment_intents.enqueue_payment_intent_webhook_deliveries",
    ) as enqueue_deliveries:
        with pytest.raises(InvalidPaymentIntentStatusTransitionError):
            confirm_payment_intent(
                db=db,
                payment_intent=payment_intent,
                xrpl_transaction_hash=XRPL_TRANSACTION_HASH,
            )

    db.commit.assert_not_called()
    db.refresh.assert_not_called()
    enqueue_deliveries.assert_not_called()
