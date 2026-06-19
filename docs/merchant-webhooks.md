# Merchant Webhooks

EuroLedger XRPL can notify each merchant when a payment intent reaches a
terminal state.

Supported events:

```text
payment_intent.confirmed
payment_intent.expired
payment_intent.cancelled
```

Webhook endpoint configuration is scoped to the authenticated merchant API key.
One merchant cannot read, update or delete another merchant's webhook endpoints.

## Configure an Endpoint

Create a webhook endpoint:

```bash
curl -s -X POST http://localhost:8000/webhook-endpoints \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -d '{
    "url": "https://example.invalid/euroledger-webhooks",
    "secret": "replace-with-a-long-random-secret",
    "enabled": true
  }' \
  | python -m json.tool
```

The `secret` is accepted on create and update, but it is not returned by the API.

List configured endpoints:

```bash
curl -s http://localhost:8000/webhook-endpoints \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

Disable an endpoint:

```bash
curl -s -X PATCH http://localhost:8000/webhook-endpoints/{endpoint_id} \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -d '{"enabled": false}' \
  | python -m json.tool
```

Delete an endpoint:

```bash
curl -i -X DELETE http://localhost:8000/webhook-endpoints/{endpoint_id} \
  -H "X-API-Key: ${MERCHANT_API_KEY}"
```

## Delivery Flow

When a payment intent transitions to `confirmed`, `expired` or `cancelled`,
EuroLedger creates one pending delivery per enabled endpoint for that merchant.

The delivery worker processes pending deliveries:

```bash
docker compose exec backend \
  python -m app.commands.webhook_worker \
  --limit 100 \
  --timeout 10 \
  --max-attempts 5
```

The Compose service runs the same worker continuously:

```bash
docker compose up -d --build webhook-worker
docker compose logs -f webhook-worker
```

## Request Headers

Each delivery is an HTTP `POST` with JSON body and these headers:

```text
X-EuroLedger-Event
X-EuroLedger-Delivery
X-EuroLedger-Timestamp
X-EuroLedger-Signature
```

The signature format is:

```text
sha256=<hex digest>
```

The signed payload is:

```text
{timestamp}.{raw_body}
```

where `timestamp` is the exact `X-EuroLedger-Timestamp` value and `raw_body` is
the exact request body bytes.

## Verify a Signature in Python

```python
import hashlib
import hmac


def verify_signature(
    *,
    secret: str,
    timestamp: str,
    raw_body: bytes,
    received_signature: str,
) -> bool:
    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, received_signature)
```

Receivers should reject requests with missing signatures. A production receiver
should also reject old timestamps to reduce replay risk.

## Example Payload

```json
{
  "type": "payment_intent.confirmed",
  "created_at": "2026-06-19T15:00:00+00:00",
  "merchant_id": "merchant-id",
  "data": {
    "object": {
      "id": "intent-id",
      "merchant_id": "merchant-id",
      "reference": "EL-TESTREFERENCE",
      "amount": "25.00",
      "currency": "EUR",
      "status": "confirmed",
      "description": "Order 123",
      "expected_destination": "rDestination",
      "xrpl_transaction_hash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
      "expires_at": "2026-06-19T15:15:00+00:00",
      "cancelled_at": null,
      "cancellation_reason": null,
      "created_at": "2026-06-19T14:55:00+00:00",
      "updated_at": "2026-06-19T15:00:00+00:00"
    }
  }
}
```

## Retries and Discards

The worker marks a delivery as:

- `delivered` when the endpoint returns any 2xx response;
- `failed` when the request fails or returns a non-2xx response and retries remain;
- `discarded` when maximum attempts are exhausted;
- `discarded` immediately when the endpoint no longer exists or is disabled.

Retry delay uses exponential backoff capped at one hour.

## Observability

Webhook worker metrics are exposed through `/metrics`:

```bash
curl -s http://localhost:8000/metrics | grep euroledger_webhook
```

Useful metrics:

```text
euroledger_webhook_delivery_worker_health
euroledger_webhook_delivery_worker_cycles_total
euroledger_webhook_deliveries_total
euroledger_webhook_delivery_worker_last_success_age_seconds
```

Prometheus alert rules cover degraded, stale and failed worker cycles, plus
discarded deliveries.

## Local Testing Tips

For a local receiver, expose a small HTTP endpoint and use its URL when creating
the webhook endpoint. Public webhook inspection services also work, but never
use production secrets or real customer data with third-party inspection tools.

After creating an endpoint, trigger a payment intent transition and run:

```bash
docker compose exec backend \
  python -m app.commands.webhook_worker \
  --limit 100 \
  --timeout 10 \
  --max-attempts 5
```
