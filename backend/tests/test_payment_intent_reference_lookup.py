from unittest.mock import Mock, patch

from app.services.payment_intents import (
    get_payment_intent_by_payment_reference,
)


def test_get_payment_intent_by_reference_normalizes_reference_to_uppercase() -> None:
    db = Mock()

    with patch(
        "app.services.payment_intents.get_payment_intent_by_reference",
        return_value=None,
    ) as get_by_reference:
        get_payment_intent_by_payment_reference(
            db,
            "el-abc123def456",
            merchant_id="merchant-id",
        )

    get_by_reference.assert_called_once_with(
        db,
        "EL-ABC123DEF456",
        merchant_id="merchant-id",
    )
