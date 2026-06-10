from decimal import Decimal
from typing import Any

from app.schemas.payment_intent import PaymentIntentDetectedPayment


class XrplTransactionParseError(ValueError):
    """Raised when an XRPL transaction cannot be parsed into a detected payment."""


def parse_xrpl_transaction_to_detected_payment(
    transaction: dict[str, Any],
) -> PaymentIntentDetectedPayment:
    reference = extract_reference_from_transaction(transaction)
    amount, currency, issuer = extract_amount_from_transaction(transaction)
    destination = extract_destination_from_transaction(transaction)
    transaction_hash = extract_transaction_hash(transaction)

    return PaymentIntentDetectedPayment(
        reference=reference,
        amount=amount,
        currency=currency,
        xrpl_transaction_hash=transaction_hash,
        destination=destination,
        issuer=issuer,
    )


def extract_reference_from_transaction(transaction: dict[str, Any]) -> str:
    memos = transaction.get("Memos", [])

    for memo_wrapper in memos:
        memo = memo_wrapper.get("Memo", {})
        memo_data = memo.get("MemoData")

        if memo_data:
            return decode_hex_string(memo_data)

    raise XrplTransactionParseError("XRPL transaction does not include a payment reference memo.")


def extract_amount_from_transaction(
    transaction: dict[str, Any],
) -> tuple[Decimal, str, str | None]:
    amount = transaction.get("Amount")

    if isinstance(amount, str):
        return drops_to_xrp(amount), "XRP", None

    if isinstance(amount, dict):
        value = amount.get("value")
        currency = amount.get("currency")
        issuer = amount.get("issuer")

        if value is None or currency is None:
            raise XrplTransactionParseError("XRPL issued currency amount is incomplete.")

        return Decimal(value), str(currency).upper(), issuer

    raise XrplTransactionParseError("XRPL transaction amount is missing or unsupported.")


def extract_destination_from_transaction(transaction: dict[str, Any]) -> str:
    destination = transaction.get("Destination")

    if not destination:
        raise XrplTransactionParseError("XRPL transaction destination is missing.")

    return str(destination)


def extract_transaction_hash(transaction: dict[str, Any]) -> str:
    transaction_hash = transaction.get("hash")

    if not transaction_hash:
        transaction_hash = transaction.get("Hash")

    if not transaction_hash:
        raise XrplTransactionParseError("XRPL transaction hash is missing.")

    return str(transaction_hash)


def decode_hex_string(value: str) -> str:
    try:
        return bytes.fromhex(value).decode("utf-8")
    except ValueError as exc:
        raise XrplTransactionParseError("XRPL memo data is not valid hexadecimal.") from exc
    except UnicodeDecodeError as exc:
        raise XrplTransactionParseError("XRPL memo data is not valid UTF-8.") from exc


def drops_to_xrp(drops: str) -> Decimal:
    return Decimal(drops) / Decimal("1000000")
