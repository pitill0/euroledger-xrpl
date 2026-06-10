import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.commands.xrpl_worker import (
    load_transactions_from_fixture,
    main,
    run_once,
)
from app.workers.xrpl_scanner import XrplTransactionScanResult


def test_load_transactions_from_fixture(tmp_path: Path) -> None:
    fixture_path = tmp_path / "transactions.json"
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]
    fixture_path.write_text(json.dumps(transactions))

    assert load_transactions_from_fixture(fixture_path) == transactions


def test_load_transactions_from_fixture_rejects_non_list_json(tmp_path: Path) -> None:
    fixture_path = tmp_path / "transactions.json"
    fixture_path.write_text(json.dumps({"TransactionType": "Payment"}))

    with pytest.raises(ValueError, match="JSON list"):
        load_transactions_from_fixture(fixture_path)


def test_load_transactions_from_fixture_rejects_non_object_transactions(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "transactions.json"
    fixture_path.write_text(json.dumps(["not-a-transaction"]))

    with pytest.raises(ValueError, match="JSON objects"):
        load_transactions_from_fixture(fixture_path)


def test_run_once_scans_given_transactions() -> None:
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]

    expected_result = XrplTransactionScanResult(
        processed=1,
        skipped=0,
        failed=0,
        confirmed_payment_intents=[],
        errors=[],
    )

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

    expected_result = XrplTransactionScanResult(
        processed=1,
        skipped=0,
        failed=0,
        confirmed_payment_intents=[],
        errors=[],
    )

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
    result = XrplTransactionScanResult(
        processed=1,
        skipped=2,
        failed=0,
        confirmed_payment_intents=[],
        errors=[],
    )

    with (
        patch("app.commands.xrpl_worker.parse_args") as parse_args,
        patch(
            "app.commands.xrpl_worker.run_once",
            return_value=result,
        ),
    ):
        parse_args.return_value.fixtures = None

        main()

    captured = capsys.readouterr()

    assert "XRPL worker scan completed" in captured.out
    assert "processed=1" in captured.out
    assert "skipped=2" in captured.out
    assert "failed=0" in captured.out


def test_main_loads_fixture_when_provided(tmp_path: Path, capsys) -> None:
    fixture_path = tmp_path / "transactions.json"
    transactions = [
        {
            "TransactionType": "Payment",
        },
    ]
    fixture_path.write_text(json.dumps(transactions))

    result = XrplTransactionScanResult(
        processed=1,
        skipped=0,
        failed=0,
        confirmed_payment_intents=[],
        errors=[],
    )

    with (
        patch("app.commands.xrpl_worker.parse_args") as parse_args,
        patch(
            "app.commands.xrpl_worker.run_once",
            return_value=result,
        ) as run_worker_once,
    ):
        parse_args.return_value.fixtures = fixture_path

        main()

    run_worker_once.assert_called_once_with(transactions)

    captured = capsys.readouterr()

    assert "processed=1" in captured.out


def test_main_prints_errors(capsys) -> None:
    result = XrplTransactionScanResult(
        processed=0,
        skipped=0,
        failed=1,
        confirmed_payment_intents=[],
        errors=["Invalid XRPL transaction"],
    )

    with (
        patch("app.commands.xrpl_worker.parse_args") as parse_args,
        patch(
            "app.commands.xrpl_worker.run_once",
            return_value=result,
        ),
    ):
        parse_args.return_value.fixtures = None

        main()

    captured = capsys.readouterr()

    assert "errors:" in captured.out
    assert "- Invalid XRPL transaction" in captured.out
