import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.commands.xrpl_worker import (
    fetch_testnet_transactions,
    load_transactions_from_fixture,
    main,
    run_once,
)
from app.workers.xrpl_scanner import XrplTransactionScanResult
from app.xrpl.settings import XrplSettings


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


def test_load_transactions_from_fixture(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "transactions.json"
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]
    fixture_path.write_text(
        json.dumps(transactions),
        encoding="utf-8",
    )

    assert load_transactions_from_fixture(fixture_path) == transactions


def test_load_transactions_from_fixture_rejects_non_list_json(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "transactions.json"
    fixture_path.write_text(
        json.dumps({"TransactionType": "Payment"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="JSON list"):
        load_transactions_from_fixture(fixture_path)


def test_load_transactions_from_fixture_rejects_non_object_transactions(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "transactions.json"
    fixture_path.write_text(
        json.dumps(["not-a-transaction"]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="JSON objects"):
        load_transactions_from_fixture(fixture_path)


def test_fetch_testnet_transactions_uses_configured_merchant_address() -> None:
    app_settings = Mock()

    xrpl_settings = XrplSettings(
        json_rpc_url="https://example.test/",
        merchant_address="rMerchantAddress",
        issuer_address=None,
        currency_code="EUR",
    )

    client = Mock()
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]

    with (
        patch(
            "app.commands.xrpl_worker.get_settings",
            return_value=app_settings,
        ),
        patch(
            "app.commands.xrpl_worker.build_xrpl_settings",
            return_value=xrpl_settings,
        ),
        patch(
            "app.commands.xrpl_worker.build_xrpl_client",
            return_value=client,
        ),
        patch(
            "app.commands.xrpl_worker.fetch_account_transactions",
            return_value=transactions,
        ) as fetch_transactions,
    ):
        result = fetch_testnet_transactions(limit=5)

    fetch_transactions.assert_called_once_with(
        client=client,
        account="rMerchantAddress",
        limit=5,
    )
    assert result == transactions


def test_fetch_testnet_transactions_requires_merchant_address() -> None:
    app_settings = Mock()

    xrpl_settings = XrplSettings(
        json_rpc_url="https://example.test/",
        merchant_address=None,
        issuer_address=None,
        currency_code="EUR",
    )

    with (
        patch(
            "app.commands.xrpl_worker.get_settings",
            return_value=app_settings,
        ),
        patch(
            "app.commands.xrpl_worker.build_xrpl_settings",
            return_value=xrpl_settings,
        ),
        pytest.raises(
            ValueError,
            match="XRPL_MERCHANT_ADDRESS must be configured",
        ),
    ):
        fetch_testnet_transactions(limit=5)


def test_run_once_scans_given_transactions() -> None:
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]

    expected_result = build_scan_result(processed=1)
    db = Mock()

    with (
        patch("app.commands.xrpl_worker.SessionLocal") as session_local,
        patch(
            "app.commands.xrpl_worker.scan_xrpl_transactions",
            return_value=expected_result,
        ) as scan_transactions,
    ):
        session_local.return_value.__enter__.return_value = db

        result = run_once(transactions)

    scan_transactions.assert_called_once_with(
        db=db,
        transactions=transactions,
    )
    assert result == expected_result


def test_run_once_uses_sample_transactions_when_not_provided() -> None:
    sample_transactions = [
        {
            "TransactionType": "Payment",
        },
    ]

    expected_result = build_scan_result(processed=1)
    db = Mock()

    with (
        patch(
            "app.commands.xrpl_worker.build_sample_transactions",
            return_value=sample_transactions,
        ) as build_samples,
        patch("app.commands.xrpl_worker.SessionLocal") as session_local,
        patch(
            "app.commands.xrpl_worker.scan_xrpl_transactions",
            return_value=expected_result,
        ) as scan_transactions,
    ):
        session_local.return_value.__enter__.return_value = db

        result = run_once()

    build_samples.assert_called_once_with()
    scan_transactions.assert_called_once_with(
        db=db,
        transactions=sample_transactions,
    )
    assert result == expected_result


def test_main_prints_scan_summary(capsys) -> None:
    result = build_scan_result(
        processed=1,
        skipped=2,
    )

    args = Namespace(
        fixtures=None,
        testnet=False,
        limit=20,
    )

    with (
        patch(
            "app.commands.xrpl_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.xrpl_worker.run_once",
            return_value=result,
        ),
    ):
        main()

    captured = capsys.readouterr()

    assert "XRPL worker scan completed" in captured.out
    assert "processed=1" in captured.out
    assert "skipped=2" in captured.out
    assert "failed=0" in captured.out


def test_main_loads_fixture_when_provided(
    tmp_path: Path,
    capsys,
) -> None:
    fixture_path = tmp_path / "transactions.json"
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]

    fixture_path.write_text(
        json.dumps(transactions),
        encoding="utf-8",
    )

    result = build_scan_result(processed=1)

    args = Namespace(
        fixtures=fixture_path,
        testnet=False,
        limit=20,
    )

    with (
        patch(
            "app.commands.xrpl_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.xrpl_worker.run_once",
            return_value=result,
        ) as run_worker_once,
    ):
        main()

    run_worker_once.assert_called_once_with(transactions)

    captured = capsys.readouterr()
    assert "processed=1" in captured.out


def test_main_fetches_testnet_transactions(capsys) -> None:
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]

    result = build_scan_result(
        failed=1,
        errors=["XRPL transaction does not include a payment reference memo."],
    )

    args = Namespace(
        fixtures=None,
        testnet=True,
        limit=5,
    )

    with (
        patch(
            "app.commands.xrpl_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.xrpl_worker.fetch_testnet_transactions",
            return_value=transactions,
        ) as fetch_transactions,
        patch(
            "app.commands.xrpl_worker.run_once",
            return_value=result,
        ) as run_worker_once,
    ):
        main()

    fetch_transactions.assert_called_once_with(limit=5)
    run_worker_once.assert_called_once_with(transactions)

    captured = capsys.readouterr()

    assert "processed=0" in captured.out
    assert "failed=1" in captured.out
    assert "payment reference memo" in captured.out


def test_main_prints_errors(capsys) -> None:
    result = build_scan_result(
        failed=1,
        errors=["Invalid XRPL transaction"],
    )

    args = Namespace(
        fixtures=None,
        testnet=False,
        limit=20,
    )

    with (
        patch(
            "app.commands.xrpl_worker.parse_args",
            return_value=args,
        ),
        patch(
            "app.commands.xrpl_worker.run_once",
            return_value=result,
        ),
    ):
        main()

    captured = capsys.readouterr()

    assert "errors:" in captured.out
    assert "- Invalid XRPL transaction" in captured.out
