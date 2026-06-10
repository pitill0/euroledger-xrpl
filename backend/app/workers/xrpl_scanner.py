from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.payment_intent import PaymentIntent
from app.workers.xrpl_payments import (
    UnsupportedXrplTransactionError,
    process_candidate_xrpl_transaction,
)


@dataclass(frozen=True)
class XrplTransactionScanResult:
    processed: int
    skipped: int
    failed: int
    confirmed_payment_intents: list[PaymentIntent]
    errors: list[str]


def scan_xrpl_transactions(
    db: Session,
    transactions: list[dict[str, Any]],
) -> XrplTransactionScanResult:
    processed = 0
    skipped = 0
    failed = 0
    confirmed_payment_intents: list[PaymentIntent] = []
    errors: list[str] = []

    for transaction in transactions:
        try:
            payment_intent = process_candidate_xrpl_transaction(
                db=db,
                transaction=transaction,
            )
        except UnsupportedXrplTransactionError:
            skipped += 1
            continue
        except Exception as exc:
            failed += 1
            errors.append(str(exc))
            continue

        processed += 1
        confirmed_payment_intents.append(payment_intent)

    return XrplTransactionScanResult(
        processed=processed,
        skipped=skipped,
        failed=failed,
        confirmed_payment_intents=confirmed_payment_intents,
        errors=errors,
    )
