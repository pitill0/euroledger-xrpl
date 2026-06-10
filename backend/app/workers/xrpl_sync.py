from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session
from xrpl.clients import JsonRpcClient

from app.repositories.worker_states import (
    get_or_create_worker_state,
    update_worker_ledger_cursor,
)
from app.workers.xrpl_scanner import (
    XrplTransactionScanResult,
    scan_xrpl_transactions,
)
from app.xrpl.account_transactions import fetch_account_transactions

XRPL_PAYMENT_WORKER_NAME = "xrpl-payment-worker"


@dataclass(frozen=True)
class XrplSynchronizationResult:
    scan_result: XrplTransactionScanResult
    fetched: int
    previous_ledger_index: int | None
    last_ledger_index: int | None


def extract_max_ledger_index(
    transactions: list[dict[str, Any]],
) -> int | None:
    ledger_indexes = [
        transaction["_ledger_index"]
        for transaction in transactions
        if isinstance(transaction.get("_ledger_index"), int)
    ]

    if not ledger_indexes:
        return None

    return max(ledger_indexes)


def synchronize_xrpl_account_transactions(
    db: Session,
    client: JsonRpcClient,
    account: str,
    *,
    limit: int = 20,
) -> XrplSynchronizationResult:
    state = get_or_create_worker_state(
        db=db,
        worker_name=XRPL_PAYMENT_WORKER_NAME,
    )

    previous_ledger_index = state.last_ledger_index

    ledger_index_min = -1
    if previous_ledger_index is not None:
        ledger_index_min = previous_ledger_index + 1

    transactions = fetch_account_transactions(
        client=client,
        account=account,
        limit=limit,
        ledger_index_min=ledger_index_min,
    )

    scan_result = scan_xrpl_transactions(
        db=db,
        transactions=transactions,
    )

    max_ledger_index = extract_max_ledger_index(transactions)

    if max_ledger_index is not None and scan_result.failed == 0:
        update_worker_ledger_cursor(
            db=db,
            state=state,
            ledger_index=max_ledger_index,
        )

    current_ledger_index = state.last_ledger_index

    return XrplSynchronizationResult(
        scan_result=scan_result,
        fetched=len(transactions),
        previous_ledger_index=previous_ledger_index,
        last_ledger_index=current_ledger_index,
    )
