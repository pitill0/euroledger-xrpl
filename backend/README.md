# EuroLedger XRPL Backend

FastAPI backend, PostgreSQL persistence, XRPL payment processing workers, merchant webhook delivery, and operational endpoints for EuroLedger XRPL.

The backend is the core runtime of EuroLedger XRPL. It creates payment intents, validates and confirms XRPL payments, expires stale intents, stores merchant configuration, and delivers signed webhook notifications to merchant systems.

## Runtime components

The backend stack is composed of:

```text
FastAPI backend
PostgreSQL
XRPL worker
Payment intent expirer
Webhook delivery worker
Prometheus metrics endpoint
Optional dashboard view
```

The services share the same backend application image but run as independent processes.

## Main capabilities

- Merchant-scoped API key authentication.
- Payment intent creation, listing, lookup, cancellation, confirmation, and CSV export.
- Idempotent payment intent creation through `Idempotency-Key`.
- Payment reference generation for XRPL memo-based reconciliation.
- XRPL Testnet transaction scanning and payment validation.
- Payment intent expiration.
- Merchant webhook endpoint management.
- Signed merchant webhook delivery with retries.
- Worker state persistence and health reporting.
- Prometheus metrics.
- Development dashboard for payment intent inspection.

## Local development

Run the local development stack from the repository root:

```bash
cd ~/projects/euroledger-xrpl
docker compose up --build
```

Run in the background:

```bash
docker compose up --build -d
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "euroledger-xrpl-backend",
  "environment": "local"
}
```

Readiness check:

```bash
curl http://localhost:8000/health/ready
```

The readiness endpoint verifies database availability and Alembic migration state.

## API documentation

When the backend is running:

```text
Swagger UI:   http://localhost:8000/docs
OpenAPI JSON: http://localhost:8000/openapi.json
```

Most merchant API endpoints require:

```text
X-API-Key: <merchant-api-key>
```

## Endpoint overview

### Authentication

```text
GET /auth/me
```

Returns the authenticated merchant for the supplied API key.

### Payment intents

```text
POST /payment-intents
GET /payment-intents
GET /payment-intents/export.csv
GET /payment-intents/by-reference/{reference}
GET /payment-intents/{payment_intent_id}
POST /payment-intents/{payment_intent_id}/confirm
POST /payment-intents/{payment_intent_id}/cancel
POST /payment-intents/detected-payments
```

Payment intents are scoped to the authenticated merchant.

### Webhook endpoints

```text
POST /webhook-endpoints
GET /webhook-endpoints
GET /webhook-endpoints/{endpoint_id}
PATCH /webhook-endpoints/{endpoint_id}
DELETE /webhook-endpoints/{endpoint_id}
POST /webhook-endpoints/{endpoint_id}/test
```

Webhook endpoint secrets are accepted on create/update and are not returned by the API.

### Webhook deliveries

```text
GET /webhook-deliveries
GET /webhook-deliveries/{delivery_id}
POST /webhook-deliveries/{delivery_id}/retry
```

Delivery records are scoped to the authenticated merchant.

### Operations

```text
GET /health
GET /health/live
GET /health/ready
GET /worker-status
GET /metrics
GET /dashboard/payment-intents/{payment_intent_id}?token=...
```

The dashboard route is intended for development and operational inspection. It is disabled unless `DASHBOARD_TOKEN` is configured.

## Database migrations

Apply all pending migrations:

```bash
docker compose exec backend alembic upgrade head
```

Create a new migration:

```bash
docker compose exec backend \
  alembic revision --autogenerate -m "migration message"
```

## Quality checks

Run Ruff linting:

```bash
docker compose exec backend ruff check app tests
```

Check Ruff formatting:

```bash
docker compose exec backend ruff format --check app tests
```

Run the test suite:

```bash
docker compose exec backend pytest
```

## Payment intent lifecycle

A normal payment intent lifecycle is:

```text
pending
→ confirmed
```

Other terminal states:

```text
expired
cancelled
```

Creation flow:

```text
Merchant API request
→ backend validates payload and API key
→ payment reference generated
→ payment intent stored
→ merchant displays payment instructions
```

Confirmation flow:

```text
XRPL transaction observed
→ memo reference extracted
→ amount/currency/destination validated
→ payment intent confirmed
→ webhook deliveries queued
→ merchant systems notified
```

## Workers

### XRPL worker

The XRPL worker runs as a separate Compose service. It scans XRPL account transactions and confirms matching payment intents.

Typical command:

```text
xrpl-worker --testnet --limit 20 --poll-interval 30
```

Configuration:

```env
XRPL_WORKER_LIMIT=20
XRPL_WORKER_POLL_INTERVAL=30
XRPL_MERCHANT_ADDRESS=r...
```

The XRPL secret or seed is not required for read-only synchronization and must not be committed.

Inspect worker logs:

```bash
docker compose logs -f xrpl-worker
```

Run a one-shot sync:

```bash
docker compose exec backend \
  xrpl-worker --testnet --limit 20
```

Run against an offline fixture:

```bash
docker compose exec backend \
  xrpl-worker --fixtures /app/fixtures/xrpl/empty_transactions.json
```

### Payment intent expirer

The expirer marks stale pending payment intents as expired.

Typical command:

```text
payment-intent-expirer --limit 100 --poll-interval 60
```

Configuration:

```env
PAYMENT_INTENT_EXPIRER_LIMIT=100
PAYMENT_INTENT_EXPIRER_POLL_INTERVAL=60
```

Inspect logs:

```bash
docker compose logs -f payment-intent-expirer
```

### Webhook delivery worker

The webhook worker sends pending merchant webhook deliveries.

Typical command:

```text
webhook-worker --limit 100 --timeout 10 --max-attempts 5 --poll-interval 10
```

Inspect logs:

```bash
docker compose logs -f webhook-worker
```

## Merchant webhooks

Merchants can configure webhook endpoints to receive signed notifications when payment intents reach terminal states.

Core docs:

```text
docs/merchant-webhooks.md
docs/merchant-webhook-operations.md
docs/webhook-notifications.md
docs/webhook-receiver-examples.md
examples/webhook_receiver_stdlib.py
```

Supported terminal events:

```text
payment_intent.confirmed
payment_intent.expired
payment_intent.cancelled
```

## Observability

Prometheus metrics are exposed at:

```text
GET /metrics
```

Related docs:

```text
docs/observability.md
docs/alerting.md
docs/alertmanager-routing.md
docs/n8n-alertmanager-workflow.md
docs/n8n-telegram-notifications.md
```

## Related documentation

- [Architecture](../docs/architecture.md)
- [Backend API and operations](../docs/backend-api-and-operations.md)
- [Payment intent expiration](../docs/payment-intent-expiration.md)
- [Payment intent dashboard](../docs/payment-intent-dashboard.md)
- [Merchant webhooks](../docs/merchant-webhooks.md)
- [Merchant webhook operations](../docs/merchant-webhook-operations.md)
- [Observability](../docs/observability.md)
- [CI](../docs/ci.md)
