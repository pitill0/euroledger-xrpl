from unittest.mock import Mock, patch

from app.models.worker_state import WorkerState
from app.workers.xrpl_scanner import XrplTransactionScanResult
from app.workers.xrpl_sync import (
    extract_max_ledger_index,
    synchronize_xrpl_account_transactions,
)


def build_scan_result(
    *,
    failed: int = 0,
) -> XrplTransactionScanResult:
    return XrplTransactionScanResult(
        processed=0,
        skipped=0,
        failed=failed,
        confirmed_payment_intents=[],
        errors=[],
    )


def test_extract_max_ledger_index() -> None:
    transactions = [
        {"_ledger_index": 100},
        {"_ledger_index": 105},
        {"TransactionType": "Payment"},
    ]

    assert extract_max_ledger_index(transactions) == 105


def test_first_sync_fetches_without_lower_ledger_bound() -> None:
    db = Mock()
    client = Mock()
    state = WorkerState(
        worker_name="xrpl-payment-worker",
        last_ledger_index=None,
    )
    transactions = [
        {
            "TransactionType": "Payment",
            "_ledger_index": 100,
        }
    ]

    with (
        patch(
            "app.workers.xrpl_sync.get_or_create_worker_state",
            return_value=state,
        ),
        patch(
            "app.workers.xrpl_sync.fetch_account_transactions",
            return_value=transactions,
        ) as fetch_transactions,
        patch(
            "app.workers.xrpl_sync.scan_xrpl_transactions",
            return_value=build_scan_result(),
        ),
        patch(
            "app.workers.xrpl_sync.update_worker_ledger_cursor",
        ) as update_cursor,
    ):
        synchronize_xrpl_account_transactions(
            db=db,
            client=client,
            account="rMerchantAddress",
            limit=20,
        )

    fetch_transactions.assert_called_once_with(
        client=client,
        account="rMerchantAddress",
        limit=20,
        ledger_index_min=-1,
    )
    update_cursor.assert_called_once_with(
        db=db,
        state=state,
        ledger_index=100,
    )


def test_incremental_sync_starts_after_previous_ledger() -> None:
    db = Mock()
    client = Mock()
    state = WorkerState(
        worker_name="xrpl-payment-worker",
        last_ledger_index=100,
    )

    with (
        patch(
            "app.workers.xrpl_sync.get_or_create_worker_state",
            return_value=state,
        ),
        patch(
            "app.workers.xrpl_sync.fetch_account_transactions",
            return_value=[],
        ) as fetch_transactions,
        patch(
            "app.workers.xrpl_sync.scan_xrpl_transactions",
            return_value=build_scan_result(),
        ),
    ):
        synchronize_xrpl_account_transactions(
            db=db,
            client=client,
            account="rMerchantAddress",
            limit=20,
        )

    fetch_transactions.assert_called_once_with(
        client=client,
        account="rMerchantAddress",
        limit=20,
        ledger_index_min=101,
    )


def test_cursor_does_not_advance_when_scan_fails() -> None:
    db = Mock()
    client = Mock()
    state = WorkerState(
        worker_name="xrpl-payment-worker",
        last_ledger_index=100,
    )
    transactions = [
        {
            "TransactionType": "Payment",
            "_ledger_index": 101,
        }
    ]

    with (
        patch(
            "app.workers.xrpl_sync.get_or_create_worker_state",
            return_value=state,
        ),
        patch(
            "app.workers.xrpl_sync.fetch_account_transactions",
            return_value=transactions,
        ),
        patch(
            "app.workers.xrpl_sync.scan_xrpl_transactions",
            return_value=build_scan_result(failed=1),
        ),
        patch(
            "app.workers.xrpl_sync.update_worker_ledger_cursor",
        ) as update_cursor,
    ):
        synchronize_xrpl_account_transactions(
            db=db,
            client=client,
            account="rMerchantAddress",
        )

    update_cursor.assert_not_called()
