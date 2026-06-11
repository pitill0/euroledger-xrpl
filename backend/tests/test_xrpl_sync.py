from unittest.mock import Mock, patch

import pytest

from app.models.worker_state import WorkerState
from app.workers.xrpl_scanner import XrplTransactionScanResult
from app.workers.xrpl_sync import (
    extract_max_ledger_index,
    synchronize_xrpl_account_transactions,
)


def build_scan_result(
    *,
    processed: int = 0,
    skipped: int = 0,
    failed: int = 0,
    errors: list[str] | None = None,
) -> XrplTransactionScanResult:
    return XrplTransactionScanResult(
        processed=processed,
        skipped=skipped,
        failed=failed,
        confirmed_payment_intents=[],
        errors=errors or [],
    )


def build_worker_state(
    *,
    last_ledger_index: int | None,
) -> WorkerState:
    return WorkerState(
        worker_name="xrpl-payment-worker",
        last_ledger_index=last_ledger_index,
        successful_cycles_total=0,
        failed_cycles_total=0,
        fetched_transactions_total=0,
        processed_transactions_total=0,
        skipped_transactions_total=0,
        failed_transactions_total=0,
    )


def test_extract_max_ledger_index() -> None:
    transactions = [
        {"_ledger_index": 100},
        {"_ledger_index": 105},
        {"TransactionType": "Payment"},
    ]

    assert extract_max_ledger_index(transactions) == 105


def test_first_sync_records_success_and_advances_cursor() -> None:
    db = Mock()
    client = Mock()
    state = build_worker_state(
        last_ledger_index=None,
    )

    transactions = [
        {
            "TransactionType": "Payment",
            "_ledger_index": 100,
        }
    ]

    scan_result = build_scan_result(
        processed=1,
    )

    with (
        patch(
            "app.workers.xrpl_sync.get_or_create_worker_state",
            return_value=state,
        ),
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_started",
        ) as mark_started,
        patch(
            "app.workers.xrpl_sync.fetch_account_transactions",
            return_value=transactions,
        ) as fetch_transactions,
        patch(
            "app.workers.xrpl_sync.scan_xrpl_transactions",
            return_value=scan_result,
        ),
        patch(
            "app.workers.xrpl_sync.update_worker_ledger_cursor",
        ) as update_cursor,
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_succeeded",
        ) as mark_succeeded,
    ):
        synchronize_xrpl_account_transactions(
            db=db,
            client=client,
            account="rMerchantAddress",
            limit=20,
        )

    mark_started.assert_called_once_with(
        db=db,
        state=state,
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

    mark_succeeded.assert_called_once_with(
        db=db,
        state=state,
        fetched=1,
        processed=1,
        skipped=0,
        failed=0,
    )


def test_incremental_sync_starts_after_previous_ledger() -> None:
    db = Mock()
    client = Mock()
    state = build_worker_state(
        last_ledger_index=100,
    )

    with (
        patch(
            "app.workers.xrpl_sync.get_or_create_worker_state",
            return_value=state,
        ),
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_started",
        ),
        patch(
            "app.workers.xrpl_sync.fetch_account_transactions",
            return_value=[],
        ) as fetch_transactions,
        patch(
            "app.workers.xrpl_sync.scan_xrpl_transactions",
            return_value=build_scan_result(),
        ),
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_succeeded",
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


def test_scan_failure_records_failed_cycle_without_advancing_cursor() -> None:
    db = Mock()
    client = Mock()
    state = build_worker_state(
        last_ledger_index=100,
    )

    transactions = [
        {
            "TransactionType": "Payment",
            "_ledger_index": 101,
        }
    ]

    scan_result = build_scan_result(
        skipped=1,
        failed=1,
        errors=["Invalid detected payment"],
    )

    with (
        patch(
            "app.workers.xrpl_sync.get_or_create_worker_state",
            return_value=state,
        ),
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_started",
        ),
        patch(
            "app.workers.xrpl_sync.fetch_account_transactions",
            return_value=transactions,
        ),
        patch(
            "app.workers.xrpl_sync.scan_xrpl_transactions",
            return_value=scan_result,
        ),
        patch(
            "app.workers.xrpl_sync.update_worker_ledger_cursor",
        ) as update_cursor,
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_failed",
        ) as mark_failed,
    ):
        synchronize_xrpl_account_transactions(
            db=db,
            client=client,
            account="rMerchantAddress",
        )

    update_cursor.assert_not_called()

    mark_failed.assert_called_once_with(
        db=db,
        state=state,
        error="Invalid detected payment",
        fetched=1,
        processed=0,
        skipped=1,
        failed=1,
    )


def test_fetch_exception_records_failed_cycle_and_reraises() -> None:
    db = Mock()
    client = Mock()
    state = build_worker_state(
        last_ledger_index=100,
    )

    error = RuntimeError("XRPL unavailable")

    with (
        patch(
            "app.workers.xrpl_sync.get_or_create_worker_state",
            return_value=state,
        ),
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_started",
        ),
        patch(
            "app.workers.xrpl_sync.fetch_account_transactions",
            side_effect=error,
        ),
        patch(
            "app.workers.xrpl_sync.mark_worker_cycle_failed",
        ) as mark_failed,
        pytest.raises(
            RuntimeError,
            match="XRPL unavailable",
        ),
    ):
        synchronize_xrpl_account_transactions(
            db=db,
            client=client,
            account="rMerchantAddress",
        )

    db.rollback.assert_called_once_with()

    mark_failed.assert_called_once_with(
        db=db,
        state=state,
        error="XRPL unavailable",
        fetched=0,
    )
