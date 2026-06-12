from prometheus_client import CollectorRegistry, Counter
from prometheus_client.exposition import generate_latest

PAYMENT_INTENT_API_REGISTRY = CollectorRegistry()

PAYMENT_INTENT_CREATION_REQUESTS = Counter(
    "euroledger_payment_intent_creation_requests",
    "Total payment intent creation requests by result.",
    labelnames=(
        "result",
        "status_code",
        "idempotent",
    ),
    registry=PAYMENT_INTENT_API_REGISTRY,
)


def record_payment_intent_creation(
    *,
    result: str,
    status_code: int,
    idempotent: bool,
) -> None:
    PAYMENT_INTENT_CREATION_REQUESTS.labels(
        result=result,
        status_code=str(status_code),
        idempotent=str(idempotent).lower(),
    ).inc()


def generate_payment_intent_api_metrics() -> bytes:
    return generate_latest(
        PAYMENT_INTENT_API_REGISTRY,
    )
