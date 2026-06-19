# Prometheus Alerting

EuroLedger XRPL includes Prometheus alerting rules for the API, XRPL worker,
payment intent expiration service and webhook delivery worker.

This stage evaluates and displays alerts locally. It does not send notifications. Alertmanager and external delivery channels are intentionally deferred to a later block.

## Rule Files

The rules are stored in:

```text
observability/prometheus/alerts.yml
```

Prometheus loads them through:

```yaml
rule_files:
  - /etc/prometheus/alerts.yml
```

## Available Alerts

### Backend

- `EuroLedgerBackendDown`: Prometheus cannot scrape the backend for at least one minute.

### XRPL Worker

- `EuroLedgerXrplWorkerDegraded`
- `EuroLedgerXrplWorkerStale`
- `EuroLedgerXrplWorkerFailureDetected`
- `EuroLedgerXrplWorkerNoRecentSuccess`

### Payment Intent Expirer

- `EuroLedgerPaymentIntentExpirerDegraded`
- `EuroLedgerPaymentIntentExpirerStale`
- `EuroLedgerPaymentIntentExpirerFailureDetected`
- `EuroLedgerPaymentIntentExpirerNoRecentSuccess`

### Webhook Worker

- `EuroLedgerWebhookWorkerDegraded`
- `EuroLedgerWebhookWorkerStale`
- `EuroLedgerWebhookWorkerFailureDetected`
- `EuroLedgerWebhookWorkerNoRecentSuccess`
- `EuroLedgerWebhookDeliveriesDiscarded`

## Validation

Validate Prometheus configuration:

```bash
docker compose run --rm --no-deps \
  --entrypoint /bin/promtool \
  prometheus \
  check config /etc/prometheus/prometheus.yml
```

Validate alert rules:

```bash
docker compose run --rm --no-deps \
  --entrypoint /bin/promtool \
  prometheus \
  check rules /etc/prometheus/alerts.yml
```

## Reload Prometheus

```bash
curl -X POST http://localhost:9090/-/reload
```

Or restart the service:

```bash
docker compose restart prometheus
```

## Inspect Alerts

Prometheus:

```text
http://localhost:9090/alerts
```

API:

```bash
curl -s http://localhost:9090/api/v1/alerts \
  | python -m json.tool
```

Grafana dashboard:

```text
EuroLedger XRPL / EuroLedger XRPL Worker
```

## Manual Verification

Backend down:

```bash
docker compose stop backend
```

XRPL worker stale:

```bash
docker compose stop xrpl-worker
```

Payment intent expirer stale:

```bash
docker compose stop payment-intent-expirer
```

Webhook worker stale:

```bash
docker compose stop webhook-worker
```

Restart each service after testing:

```bash
docker compose start backend xrpl-worker payment-intent-expirer webhook-worker
```

## Alert States

- `inactive`: expression is false;
- `pending`: expression is true but the `for` duration has not elapsed;
- `firing`: expression remains true after the `for` duration.

## Notification Delivery

Alertmanager is not part of this block. A later block can add routing, grouping, inhibition and delivery channels such as email, Slack, Telegram or webhooks.
