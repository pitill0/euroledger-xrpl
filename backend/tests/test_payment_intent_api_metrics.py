from uuid import uuid4

from app.services.payment_intent_api_metrics import (
    PAYMENT_INTENT_CREATION_REQUESTS,
    generate_payment_intent_api_metrics,
    record_payment_intent_creation,
)


def test_record_created_idempotent_payment_intent() -> None:
    unique_result = f"created-{uuid4()}"

    record_payment_intent_creation(
        result=unique_result,
        status_code=201,
        idempotent=True,
    )

    metrics = generate_payment_intent_api_metrics().decode()

    expected_labels = f'idempotent="true",result="{unique_result}",status_code="201"'

    assert f"euroledger_payment_intent_creation_requests_total{{{expected_labels}}} 1.0" in metrics


def test_record_replayed_payment_intent() -> None:
    unique_result = f"replayed-{uuid4()}"

    record_payment_intent_creation(
        result=unique_result,
        status_code=200,
        idempotent=True,
    )

    metrics = generate_payment_intent_api_metrics().decode()

    expected_labels = f'idempotent="true",result="{unique_result}",status_code="200"'

    assert f"euroledger_payment_intent_creation_requests_total{{{expected_labels}}} 1.0" in metrics


def test_record_non_idempotent_creation() -> None:
    unique_result = f"created-{uuid4()}"

    record_payment_intent_creation(
        result=unique_result,
        status_code=201,
        idempotent=False,
    )

    metrics = generate_payment_intent_api_metrics().decode()

    expected_labels = f'idempotent="false",result="{unique_result}",status_code="201"'

    assert f"euroledger_payment_intent_creation_requests_total{{{expected_labels}}} 1.0" in metrics


def test_metric_is_registered_as_counter() -> None:
    metric = PAYMENT_INTENT_CREATION_REQUESTS

    assert metric._name == ("euroledger_payment_intent_creation_requests")
