# EuroLedger XRPL WooCommerce Gateway

Experimental WooCommerce payment gateway for EuroLedger XRPL.

The gateway can create backend payment intents during checkout in a local or
testnet environment and receive signed backend webhooks that move confirmed
WooCommerce orders to processing or cancel on-hold orders when payment intents
expire or are cancelled.

## Current Scope

- Registers a WooCommerce payment gateway.
- Adds admin settings for:
  - enable/disable;
  - checkout title;
  - checkout description;
  - EuroLedger backend API base URL;
  - merchant API key;
  - test mode;
  - debug logging;
  - webhook secret;
  - optional dashboard base URL for admin order links.
- Keeps the gateway disabled by default.
- Provides an admin-only backend connection check.
- Creates backend payment intents during checkout.
- Stores payment intent id, reference and status on the WooCommerce order.
- Leaves the order `on-hold` until an external confirmation flow is added.
- Shows basic payment instructions on the order received page.
- Receives signed EuroLedger webhooks, moves confirmed orders to `processing` and cancels on-hold orders for expired or cancelled intents.
- Shows EuroLedger payment metadata on the WooCommerce admin order screen.
- Shows a compact EuroLedger status column in WooCommerce order lists.

## Install Locally

Copy or symlink this folder into WordPress:

```text
wp-content/plugins/euroledger-xrpl-gateway
```

Then activate:

```bash
wp plugin activate euroledger-xrpl-gateway
```

Or activate it from the WordPress admin plugins screen.

## Configure

Open:

```text
WooCommerce > Settings > Payments > EuroLedger XRPL
```

Set:

```text
API base URL: http://localhost:8000
Merchant API key: <merchant-api-key>
Webhook secret: <shared-webhook-secret>
Dashboard base URL: <optional-dashboard-url>
Test mode: enabled
```

Use **Check backend connection** to verify:

1. the backend responds to `GET /health`;
2. the configured merchant API key is accepted by `GET /auth/me`.

Only enable the gateway in local/test environments. Use the webhook secret when
creating the backend webhook endpoint for this WordPress site.

## Checkout Flow

When a customer selects EuroLedger XRPL at checkout, the plugin:

1. creates `POST /payment-intents` in the backend;
2. sends an `Idempotency-Key` based on the WooCommerce order id;
3. stores these order metadata keys:
   - `_euroledger_payment_intent_id`;
   - `_euroledger_payment_intent_reference`;
   - `_euroledger_payment_intent_status`;
   - `_euroledger_payment_intent_created_at`;
4. sets the order status to `on-hold`;
5. redirects to the order received page with basic payment instructions.

## Admin Order Screen

Orders with EuroLedger metadata show an **EuroLedger XRPL payment** panel in the
WooCommerce order edit screen. The panel includes the payment intent id, payment reference, EuroLedger status,
XRPL transaction hash and the latest webhook delivery metadata. It also provides
copy actions for operational identifiers and, when **Dashboard base URL** is
configured, a **View in EuroLedger** link for the payment intent.

The dashboard link is built as:

```text
<Dashboard base URL>/payment-intents/<payment-intent-id>
```

For local backend development, set **Dashboard base URL** to the token-protected
HTML dashboard base URL:

```text
http://localhost:8000/dashboard?token=<dashboard-token>
```

The gateway preserves query parameters and builds order links as:

```text
http://localhost:8000/dashboard/payment-intents/<payment-intent-id>?token=<dashboard-token>
```

Set the matching `DASHBOARD_TOKEN` value in the backend environment. Leave
**Dashboard base URL** empty to hide the button.

This panel uses WooCommerce order metadata accessors and is compatible with HPOS.

## Admin Orders List

WooCommerce order lists include an **EuroLedger** column for orders with
EuroLedger metadata. The column shows a compact payment status badge, the
payment reference and a **View** link when **Dashboard base URL** is configured.
Orders without EuroLedger metadata show an empty dash.

The column is registered for both the legacy WooCommerce orders table and the
HPOS orders screen.

## Webhook Receiver

The plugin exposes a signed webhook receiver at:

```text
/wp-json/euroledger-xrpl/v1/webhook
```

Configure a backend merchant webhook endpoint with that URL and the same
**Webhook secret** configured in the gateway settings. In the local Compose
environment, when WordPress is connected to the backend network, the backend can
usually reach WordPress at:

```text
http://euroledger-wp-dev/wp-json/euroledger-xrpl/v1/webhook
```

The receiver verifies the EuroLedger HMAC headers and handles
`payment_intent.confirmed`, `payment_intent.expired` and
`payment_intent.cancelled` events. It finds the WooCommerce order by
`_euroledger_payment_intent_id`, stores the latest webhook metadata and moves the
order from `on-hold` to `processing` when confirmed. Expired and cancelled intents
move on-hold orders to `cancelled` and store terminal metadata such as expiry,
cancellation time and cancellation reason when available. Repeated webhooks are
idempotent: metadata is refreshed and destructive status changes are only applied
while the order is still on hold.

Create the backend endpoint from the host with a merchant API key. In the local
WooCommerce dev environment, prefer the `rest_route` URL because it avoids
WordPress canonical redirects that can turn signed webhook calls into HTML
responses:

```bash
curl -s -X POST http://localhost:8000/webhook-endpoints \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://euroledger-wp-dev/?rest_route=/euroledger-xrpl/v1/webhook",
    "secret": "test-secret-123456789",
    "enabled": true
  }' | python -m json.tool
```

After a backend payment intent is confirmed, run the webhook worker or let the
Compose service process the delivery:

```bash
sudo docker compose exec backend python -m app.commands.webhook_worker \
  --limit 100 \
  --timeout 10 \
  --max-attempts 5
```

A manual worker run can report `processed=0` when the automatic worker service
has already delivered the pending webhook. Check `/webhook-deliveries` for the
authoritative delivery status.

For the full local E2E procedure, see:

```text
../../docs/woocommerce-webhook-dev-flow.md
```
