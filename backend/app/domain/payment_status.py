from app.models.payment_intent import PaymentIntentStatus

TERMINAL_PAYMENT_INTENT_STATUSES = {
    PaymentIntentStatus.confirmed,
    PaymentIntentStatus.expired,
    PaymentIntentStatus.cancelled,
}

VALID_PAYMENT_INTENT_TRANSITIONS = {
    PaymentIntentStatus.pending: {
        PaymentIntentStatus.confirmed,
        PaymentIntentStatus.expired,
        PaymentIntentStatus.cancelled,
    },
    PaymentIntentStatus.confirmed: set(),
    PaymentIntentStatus.expired: set(),
    PaymentIntentStatus.cancelled: set(),
}


def is_terminal_payment_intent_status(status: PaymentIntentStatus) -> bool:
    return status in TERMINAL_PAYMENT_INTENT_STATUSES


def can_transition_payment_intent_status(
    current_status: PaymentIntentStatus,
    target_status: PaymentIntentStatus,
) -> bool:
    return target_status in VALID_PAYMENT_INTENT_TRANSITIONS[current_status]
