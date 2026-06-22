# EuroLedger XRPL WooCommerce Gateway

Experimental WooCommerce payment gateway for EuroLedger XRPL.

The gateway can create backend payment intents during checkout in a local or
testnet environment. It does not confirm orders automatically yet.

## Current Scope

- Registers a WooCommerce payment gateway.
- Adds admin settings for:
  - enable/disable;
  - checkout title;
  - checkout description;
  - EuroLedger backend API base URL;
  - merchant API key;
  - test mode;
  - debug logging.
- Keeps the gateway disabled by default.
- Provides an admin-only backend connection check.
- Creates backend payment intents during checkout.
- Stores payment intent id, reference and status on the WooCommerce order.
- Leaves the order `on-hold` until an external confirmation flow is added.
- Shows basic payment instructions on the order received page.

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
Test mode: enabled
```

Use **Check backend connection** to verify:

1. the backend responds to `GET /health`;
2. the configured merchant API key is accepted by `GET /auth/me`.

Only enable the gateway in local/test environments. Real checkout still needs
payment confirmation from EuroLedger webhooks before orders can be marked as
paid.

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

## Next Integration Block

The next block should add backend-to-WordPress confirmation handling so orders
can move from `on-hold` to `processing` or `completed` after the XRPL payment is
confirmed.
