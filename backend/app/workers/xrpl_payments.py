from typing import Any

from sqlalchemy.orm import Session

from app.models.payment_intent import PaymentIntent
from app.xrpl.payments import process_xrpl_payment_transaction


class XrplWorkerError(Exception):
    """Base exception for XRPL worker errors."""


class UnsupportedXrplTransactionError(XrplWorkerError):
    """Raised when a transaction is not supported by the XRPL payment worker."""


def is_candidate_payment_transaction(transaction: dict[str, Any]) -> bool:
    return transaction.get("TransactionType") == "Payment"


def process_candidate_xrpl_transaction(
    db: Session,
    transaction: dict[str, Any],
) -> PaymentIntent:
    if not is_candidate_payment_transaction(transaction):
        raise UnsupportedXrplTransactionError("XRPL worker only supports Payment transactions.")

    return process_xrpl_payment_transaction(
        db=db,
        transaction=transaction,
    )
