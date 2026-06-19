# Merchant Webhook Operations

This runbook summarizes the operational flow for merchant webhooks in
EuroLedger XRPL.

Use it when validating a merchant integration locally or when debugging webhook
delivery issues.

## Current Design Decisions

- Webhook endpoints are scoped to the authenticated merchant API key.
- Payment intent events create one delivery per enabled endpoint.
- Manual retry does not create a new event. It requeues an existing delivery.
- Endpoint test events are sent immediately and are not stored in
  `webhook_deliveries`.
- Cross-merchant endpoint and delivery access returns `404`.
- When the backend runs in Compose, `127.0.0.1` from the backend container is
  the container itself, not the host.

## 1. Start a Local Receiver

For local tests without extra dependencies:

```bash
EUROLEDGER_WEBHOOK_SECRET="test-secret-123456789" \
  python examples/webhook_receiver_stdlib.py \
  --host 0.0.0.0 \
  --port 9999
```

If the backend runs in Compose, use a host alias when configuring the endpoint:

```text
http://host.containers.internal:9999/webhook
http://host.docker.internal:9999/webhook
```

## 2. Create a Webhook Endpoint

```bash
curl -s -X POST http://localhost:8000/webhook-endpoints \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -d '{
    "url": "http://host.containers.internal:9999/webhook",
    "secret": "test-secret-123456789",
    "enabled": true
  }' \
  | python -m json.tool
```

Capture the returned endpoint id:

```bash
ENDPOINT_ID="replace-with-endpoint-id"
```

## 3. Send a Test Event

```bash
curl -s -X POST "http://localhost:8000/webhook-endpoints/${ENDPOINT_ID}/test" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

Expected result:

- `delivered: true` when the receiver returns 2xx;
- `delivered: false` plus `error_message` or `response_status_code` otherwise.

## 4. Trigger a Real Payment Intent Event

Create a payment intent:

```bash
PAYMENT_INTENT_ID=$(
  curl -s -X POST http://localhost:8000/payment-intents \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${MERCHANT_API_KEY}" \
    -H "Idempotency-Key: webhook-ops-test-$(date +%s)" \
    -d '{
      "amount": "10.00",
      "currency": "EUR",
      "description": "Webhook operations test",
      "expires_in_seconds": 900
    }' \
    | tee /tmp/euroledger-payment-intent.json \
    | python -c 'import json,sys; print(json.load(sys.stdin)["id"])'
)

python -m json.tool /tmp/euroledger-payment-intent.json
```

Cancel it to generate `payment_intent.cancelled`:

```bash
curl -s -X POST \
  "http://localhost:8000/payment-intents/${PAYMENT_INTENT_ID}/cancel" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -d '{"reason": "Webhook operations test"}' \
  | python -m json.tool
```

## 5. Inspect Deliveries

```bash
curl -s http://localhost:8000/webhook-deliveries \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | tee /tmp/euroledger-webhook-deliveries.json \
  | python -m json.tool
```

Filter failed deliveries:

```bash
curl -s "http://localhost:8000/webhook-deliveries?status_filter=failed" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

## 6. Run the Delivery Worker

One-shot run:

```bash
docker compose exec backend \
  python -m app.commands.webhook_worker \
  --limit 100 \
  --timeout 10 \
  --max-attempts 5
```

Continuous Compose service:

```bash
docker compose up -d --build webhook-worker
docker compose logs -f webhook-worker
```

## 7. Retry a Failed or Discarded Delivery

```bash
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

Expected result:

- `status: pending`;
- `attempt_count: 0`;
- `last_attempt_at: null`;
- cleared response/error fields.

Already delivered deliveries return `409`.

## 8. Check Metrics and Alerts

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

Webhook worker alerts are routed through the same Alertmanager and n8n flow as
the other EuroLedger worker alerts.

## Related Documentation

- [`merchant-webhooks.md`](merchant-webhooks.md)
- [`webhook-receiver-examples.md`](webhook-receiver-examples.md)
- [`n8n-alertmanager-workflow.md`](n8n-alertmanager-workflow.md)
- [`n8n-telegram-notifications.md`](n8n-telegram-notifications.md)
