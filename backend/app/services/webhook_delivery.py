from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.models.webhook import WebhookDelivery, WebhookDeliveryStatus
from app.repositories.webhook_deliveries import list_due_webhook_deliveries
from app.services.webhook_signing import build_webhook_headers, serialize_webhook_payload

DEFAULT_WEBHOOK_TIMEOUT_SECONDS = 10.0
DEFAULT_WEBHOOK_MAX_ATTEMPTS = 5
MAX_RESPONSE_BODY_LENGTH = 2000


@dataclass(frozen=True)
class WebhookHttpResponse:
    status_code: int
    body: str


@dataclass(frozen=True)
class WebhookDeliveryRunResult:
    processed: int
    delivered: int
    failed: int
    discarded: int
    limit: int


def utc_now() -> datetime:
    return datetime.now(UTC)


def calculate_next_attempt_at(
    *,
    now: datetime,
    attempt_count: int,
) -> datetime:
    delay_seconds = min(
        3600,
        60 * (2 ** max(attempt_count - 1, 0)),
    )

    return now + timedelta(seconds=delay_seconds)


def truncate_response_body(
    body: str,
) -> str:
    return body[:MAX_RESPONSE_BODY_LENGTH]


def validate_webhook_delivery_url(
    url: str,
) -> str:
    parsed_url = urlsplit(url)

    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError("Webhook URL must use http or https.")

    if not parsed_url.netloc:
        raise ValueError("Webhook URL must include a host.")

    return url


def post_webhook(
    *,
    url: str,
    raw_body: bytes,
    headers: dict[str, str],
    timeout: float,
) -> WebhookHttpResponse:
    request = Request(
        url=validate_webhook_delivery_url(url),
        data=raw_body,
        headers=headers,
        method="POST",
    )

    try:
        # URL scheme is validated above.
        with urlopen(  # nosec B310
            request,
            timeout=timeout,
        ) as response:
            body = response.read().decode("utf-8", errors="replace")
            return WebhookHttpResponse(
                status_code=response.status,
                body=body,
            )
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return WebhookHttpResponse(
            status_code=exc.code,
            body=body,
        )


def mark_delivery_discarded(
    delivery: WebhookDelivery,
    *,
    now: datetime,
    error_message: str,
) -> None:
    delivery.status = WebhookDeliveryStatus.discarded
    delivery.last_attempt_at = now
    delivery.next_attempt_at = None
    delivery.error_message = error_message


def deliver_webhook(
    delivery: WebhookDelivery,
    *,
    now: datetime,
    timeout: float = DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
    max_attempts: int = DEFAULT_WEBHOOK_MAX_ATTEMPTS,
) -> WebhookDeliveryStatus:
    endpoint = delivery.endpoint

    if endpoint is None:
        mark_delivery_discarded(
            delivery,
            now=now,
            error_message="Webhook endpoint no longer exists.",
        )
        return WebhookDeliveryStatus.discarded

    if not endpoint.enabled:
        mark_delivery_discarded(
            delivery,
            now=now,
            error_message="Webhook endpoint is disabled.",
        )
        return WebhookDeliveryStatus.discarded

    raw_body = serialize_webhook_payload(delivery.payload)
    timestamp = int(now.timestamp())
    headers = build_webhook_headers(
        event_type=delivery.event_type,
        delivery_id=delivery.id,
        secret=endpoint.secret,
        timestamp=timestamp,
        raw_body=raw_body,
    )

    delivery.attempt_count += 1
    delivery.last_attempt_at = now
    delivery.error_message = None

    try:
        response = post_webhook(
            url=endpoint.url,
            raw_body=raw_body,
            headers=headers,
            timeout=timeout,
        )
    except (TimeoutError, URLError, OSError) as exc:
        delivery.response_status_code = None
        delivery.response_body = None
        delivery.error_message = str(exc)

        if delivery.attempt_count >= max_attempts:
            delivery.status = WebhookDeliveryStatus.discarded
            delivery.next_attempt_at = None
            return WebhookDeliveryStatus.discarded

        delivery.status = WebhookDeliveryStatus.failed
        delivery.next_attempt_at = calculate_next_attempt_at(
            now=now,
            attempt_count=delivery.attempt_count,
        )
        return WebhookDeliveryStatus.failed

    delivery.response_status_code = response.status_code
    delivery.response_body = truncate_response_body(response.body)

    if 200 <= response.status_code < 300:
        delivery.status = WebhookDeliveryStatus.delivered
        delivery.next_attempt_at = None
        return WebhookDeliveryStatus.delivered

    delivery.error_message = f"Webhook endpoint returned HTTP {response.status_code}."

    if delivery.attempt_count >= max_attempts:
        delivery.status = WebhookDeliveryStatus.discarded
        delivery.next_attempt_at = None
        return WebhookDeliveryStatus.discarded

    delivery.status = WebhookDeliveryStatus.failed
    delivery.next_attempt_at = calculate_next_attempt_at(
        now=now,
        attempt_count=delivery.attempt_count,
    )

    return WebhookDeliveryStatus.failed


def process_due_webhook_deliveries(
    db: Session,
    *,
    limit: int,
    timeout: float = DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
    max_attempts: int = DEFAULT_WEBHOOK_MAX_ATTEMPTS,
    now: datetime | None = None,
) -> WebhookDeliveryRunResult:
    run_started_at = now or utc_now()
    deliveries = list_due_webhook_deliveries(
        db=db,
        now=run_started_at,
        limit=limit,
    )

    delivered = 0
    failed = 0
    discarded = 0

    for delivery in deliveries:
        result = deliver_webhook(
            delivery,
            now=run_started_at,
            timeout=timeout,
            max_attempts=max_attempts,
        )

        if result == WebhookDeliveryStatus.delivered:
            delivered += 1
        elif result == WebhookDeliveryStatus.failed:
            failed += 1
        elif result == WebhookDeliveryStatus.discarded:
            discarded += 1

    db.commit()

    return WebhookDeliveryRunResult(
        processed=len(deliveries),
        delivered=delivered,
        failed=failed,
        discarded=discarded,
        limit=limit,
    )
