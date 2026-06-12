# Generic Webhook Notifications

EuroLedger XRPL can deliver Alertmanager notifications to any HTTP endpoint that accepts the standard Alertmanager webhook payload.

The webhook integration is optional and is enabled through a Compose overlay. The default stack continues to use local sink receivers and does not attempt external delivery.

## Design

The webhook mode uses:

```text
docker-compose.yml
docker-compose.webhook.yml
```

The overlay replaces the active Alertmanager configuration with:

```text
observability/alertmanager/alertmanager-webhook.yml
```

The destination URL is read from an untracked local file:

```text
observability/alertmanager/secrets/webhook_url
```

The URL is not stored in Git.

## Supported Destinations

Any endpoint that accepts Alertmanager's generic webhook JSON payload can be used, including:

- n8n;
- a custom FastAPI or Flask receiver;
- an internal automation service;
- a webhook relay;
- another notification gateway.

Provider-specific webhooks such as Slack or Microsoft Teams often require payload transformation. An n8n workflow or a small relay service can perform that transformation.

## Configure the Webhook URL

Create the secrets directory:

```bash
mkdir -p observability/alertmanager/secrets
```

Write the destination URL:

```bash
printf '%s\n' \
  'https://example.invalid/replace-with-real-webhook' \
  > observability/alertmanager/secrets/webhook_url
```

Protect the file:

```bash
chmod 644 observability/alertmanager/secrets/webhook_url
```

Do not commit this file.

## Validate the Configuration

Validate the webhook-enabled Alertmanager configuration:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.webhook.yml \
  run --rm --no-deps \
  --entrypoint /bin/amtool \
  alertmanager \
  check-config /etc/alertmanager/alertmanager.yml
```

## Enable Webhook Delivery

Recreate Alertmanager using the overlay:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.webhook.yml \
  up -d --force-recreate alertmanager
```

Prometheus does not need to be reconfigured because it already sends alerts to Alertmanager.

## Disable Webhook Delivery

Recreate Alertmanager with the base Compose file only:

```bash
docker compose \
  -f docker-compose.yml \
  up -d --force-recreate alertmanager
```

This restores the sink receivers from the base configuration.

## Routing

Critical alerts use:

```text
critical-webhook
```

Warning alerts use:

```text
warning-webhook
```

Both receivers use the same URL file. Routing remains separated so different destinations can be introduced later without changing alert rules.

Resolved notifications are enabled:

```yaml
send_resolved: true
```

The receiver therefore gets both firing and resolved events.

## Test Delivery

The easiest end-to-end test is to trigger the backend-down alert:

```bash
docker compose stop backend
```

Wait until `EuroLedgerBackendDown` is firing, then inspect the destination endpoint.

Restore the backend:

```bash
docker compose start backend
```

A resolved notification should follow after Prometheus and Alertmanager observe recovery.

## Inspect Alertmanager

Logs:

```bash
docker compose logs -f alertmanager
```

Active alerts:

```bash
curl -s http://localhost:9093/api/v2/alerts \
  | python -m json.tool
```

Status:

```bash
curl -s http://localhost:9093/api/v2/status \
  | python -m json.tool
```

## Payload

Alertmanager sends an HTTP POST containing grouped alert data. Common fields include:

```text
receiver
status
groupLabels
commonLabels
commonAnnotations
alerts
externalURL
version
groupKey
```

Each item in `alerts` includes labels, annotations, start time, end time and a generator URL.

## n8n

For n8n:

1. create a Webhook node accepting `POST`;
2. activate the workflow;
3. copy the production webhook URL;
4. store that URL in `observability/alertmanager/secrets/webhook_url`;
5. enable the Compose overlay.

The workflow can then branch by:

```text
body.status
body.commonLabels.severity
body.commonLabels.component
```

## Security

- Treat the webhook URL as a secret.
- Use HTTPS for external destinations.
- Restrict the receiver by network or authentication when possible.
- Rotate the URL if it is exposed.
- Never commit the local `webhook_url` file.
- Inspect payloads before forwarding them to public chat systems.

## Future Extensions

The existing routing can later be extended with:

- separate critical and warning URL files;
- bearer-token authentication;
- basic authentication;
- mTLS;
- retry relays;
- provider-specific formatting;
- separate n8n workflows by component.
