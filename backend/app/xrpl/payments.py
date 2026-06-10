from typing import Any

from sqlalchemy.orm import Session

from app.models.payment_intent import PaymentIntent
from app.services.payment_intents import validate_and_confirm_detected_payment
from app.xrpl.transactions import parse_xrpl_transaction_to_detected_payment


def process_xrpl_payment_transaction(
    db: Session,
    transaction: dict[str, Any],
) -> PaymentIntent:
    detected_payment = parse_xrpl_transaction_to_detected_payment(transaction)

    return validate_and_confirm_detected_payment(
        db=db,
        detected_payment=detected_payment,
    )
