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

Send a signed test event to an endpoint:

```bash
curl -s -X POST http://localhost:8000/webhook-endpoints/{endpoint_id}/test \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

The test event is sent immediately and is not stored as a webhook delivery. Use
it to validate the receiver URL, signature verification and network reachability
before triggering real payment intent events.

For local testing, this repository includes a stdlib-only receiver:

```bash
EUROLEDGER_WEBHOOK_SECRET="replace-with-a-long-random-secret" \
  python examples/webhook_receiver_stdlib.py \
  --host 0.0.0.0 \
  --port 9999
```

If the backend runs inside Compose, do not configure the webhook endpoint with
`127.0.0.1` unless the receiver also runs inside the same container. From a
container, `127.0.0.1` points back to that container. Use the host alias exposed
by your runtime, for example:

```text
http://host.containers.internal:9999/webhook
http://host.docker.internal:9999/webhook
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

Receiver examples for FastAPI, Flask and Node.js are available in
[`webhook-receiver-examples.md`](webhook-receiver-examples.md).

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

## Inspect Deliveries

Webhook delivery records are scoped to the authenticated merchant API key.

List recent deliveries:

```bash
curl -s http://localhost:8000/webhook-deliveries \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

Filter deliveries by status:

```bash
curl -s "http://localhost:8000/webhook-deliveries?status_filter=failed" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

Read a single delivery:

```bash
curl -s http://localhost:8000/webhook-deliveries/{delivery_id} \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

Cross-merchant deliveries are hidden and return `404`.

## Manual Retry

Use manual retry when a delivery is `failed` or `discarded` and the merchant
endpoint is ready to receive it again.

```bash
curl -s -X POST http://localhost:8000/webhook-deliveries/{delivery_id}/retry \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

Manual retry resets the delivery to:

- `status: pending`;
- `attempt_count: 0`;
- `next_attempt_at: now`;
- no stored response status, response body or error message.

Already delivered webhook deliveries cannot be retried and return `409`.

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

To test the retry flow locally, create an endpoint pointing to a closed local
port:

```bash
curl -s -X POST http://localhost:8000/webhook-endpoints \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -d '{
    "url": "http://127.0.0.1:9999/webhook",
    "secret": "test-secret-123456789",
    "enabled": true
  }' \
  | python -m json.tool
```

Create a payment intent:

```bash
PAYMENT_INTENT_ID=$(
  curl -s -X POST http://localhost:8000/payment-intents \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${MERCHANT_API_KEY}" \
    -H "Idempotency-Key: webhook-retry-test-$(date +%s)" \
    -d '{
      "amount": "10.00",
      "currency": "EUR",
      "description": "Manual webhook retry test",
      "expires_in_seconds": 900
    }' \
    | tee /tmp/euroledger-payment-intent.json \
    | python -c 'import json,sys; print(json.load(sys.stdin)["id"])'
)

python -m json.tool /tmp/euroledger-payment-intent.json
```

Trigger a real transition:

```bash
curl -s -X POST \
  "http://localhost:8000/payment-intents/${PAYMENT_INTENT_ID}/cancel" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -d '{"reason": "Manual webhook retry test"}' \
  | python -m json.tool
```

Run the worker once. The closed port should make the delivery fail:

```bash
docker compose exec backend \
  python -m app.commands.webhook_worker \
  --limit 100 \
  --timeout 10 \
  --max-attempts 5
```

Capture the delivery id and retry it:

```bash
curl -s http://localhost:8000/webhook-deliveries \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | tee /tmp/euroledger-webhook-deliveries.json \
  | python -m json.tool

DELIVERY_ID=$(
  python -c '
import json

print(json.load(open("/tmp/euroledger-webhook-deliveries.json"))["items"][0]["id"])
'
)

curl -s -X POST "http://localhost:8000/webhook-deliveries/${DELIVERY_ID}/retry" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```
