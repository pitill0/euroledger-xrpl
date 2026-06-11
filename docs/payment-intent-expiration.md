# Payment Intent Expiration

EuroLedger XRPL automatically expires pending payment intents after their configured expiration time.

## Expiration Rules

A payment intent can be expired automatically only when:

- its current status is `pending`;
- its `expires_at` timestamp is earlier than or equal to the current time.

The resulting transition is:

```text
pending -> expired
```

Confirmed, cancelled or already expired payment intents are not modified.

## Payment Intent Lifetime

When creating a payment intent, clients can provide:

```json
{
  "amount": "25.00",
  "currency": "EUR",
  "expires_in_seconds": 900
}
```

The default lifetime is 900 seconds.

The accepted range is:

```text
60 seconds to 86400 seconds
```

## Compose Service

The expiration process runs as an independent Compose service:

```text
payment-intent-expirer
```

Its command is equivalent to:

```text
payment-intent-expirer --limit 100 --poll-interval 60
```

Configuration:

```env
PAYMENT_INTENT_EXPIRER_LIMIT=100
PAYMENT_INTENT_EXPIRER_POLL_INTERVAL=60
```

## Start the Service

Start the complete stack:

```bash
docker compose up -d --build
```

Start only the expirer and its dependencies:

```bash
docker compose up -d payment-intent-expirer
```

## Logs

Inspect recent logs:

```bash
docker compose logs --tail 100 payment-intent-expirer
```

Follow logs:

```bash
docker compose logs -f payment-intent-expirer
```

A successful cycle produces an event similar to:

```text
event=payment_intent_expiration_completed expired=0 limit=100
```

## Independent Operation

Stop only the expiration service:

```bash
docker compose stop payment-intent-expirer
```

Start it again:

```bash
docker compose start payment-intent-expirer
```

Recreate it after a configuration or image change:

```bash
docker compose up -d --build payment-intent-expirer
```

The API, PostgreSQL and XRPL worker remain independent.

## One-shot Execution

Run one expiration cycle manually:

```bash
docker compose exec backend \
  payment-intent-expirer --limit 100
```

## Polling Execution

Run polling interactively:

```bash
docker compose exec backend \
  payment-intent-expirer \
  --limit 100 \
  --poll-interval 5
```

Stop it with `Ctrl+C`.

## Concurrency

Expired pending payment intents are selected using:

```text
FOR UPDATE SKIP LOCKED
```

This prevents concurrent expiration processes from handling the same locked rows simultaneously.

## Operational Notes

- The service does not expose network ports.
- It reuses the backend image.
- It connects directly to PostgreSQL.
- It uses structured logs.
- An unexpected cycle error is logged and does not terminate polling.
- `SIGINT` and `SIGTERM` produce a clean shutdown.
