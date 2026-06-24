# EuroLedger XRPL WooCommerce Gateway v0.1.1

## Summary

EuroLedger XRPL WooCommerce Gateway v0.1.1 is the first functional development release of the WooCommerce integration.

This release provides a complete classic-checkout payment flow between WooCommerce and EuroLedger XRPL:

- WooCommerce creates EuroLedger payment intents during checkout.
- Customers receive a payment reference and can track payment status from the order pages.
- EuroLedger sends signed webhooks back to WordPress.
- WooCommerce updates orders automatically when payment intents are confirmed, cancelled, or expired.
- Store administrators get improved visibility from the order detail screen, the orders list, and the backend dashboard.
- Development smoke scripts and packaging helpers are included to validate and build the plugin ZIP.

## Supported flow

### Customer checkout

- Classic WooCommerce checkout is supported.
- The customer selects **EuroLedger XRPL** as the payment method.
- The plugin creates a backend payment intent using the configured EuroLedger API base URL and merchant API key.
- The WooCommerce order is placed on hold.
- The customer sees:
  - payment reference,
  - payment intent ID,
  - EuroLedger payment status,
  - XRPL transaction hash when available,
  - cancellation reason when applicable.

### Payment lifecycle

The plugin currently handles the following backend states:

| EuroLedger payment intent | WooCommerce order result |
| --- | --- |
| `pending` | `on-hold` |
| `confirmed` | `processing` |
| `cancelled` | `cancelled` |
| `expired` | `cancelled` |

Webhook handling is idempotent. If an order is no longer `on-hold`, the plugin refreshes EuroLedger metadata and adds an order note, but avoids overwriting an already-progressed WooCommerce order state.

## Store administration

### Order detail panel

WooCommerce order detail pages include a dedicated **EuroLedger XRPL payment** panel showing:

- payment intent ID,
- payment reference,
- EuroLedger status badge,
- created / confirmed / expires / cancelled timestamps,
- XRPL transaction hash,
- cancellation reason,
- last webhook event,
- last webhook delivery ID,
- last webhook timestamp,
- quick copy actions,
- optional **View in EuroLedger** dashboard link.

### Orders list

The WooCommerce orders list includes a compact **EuroLedger** column with:

- status badge,
- payment reference,
- dashboard link when configured.

Both the legacy orders table and the HPOS orders screen are supported.

## Backend dashboard

This release adds a simple backend dashboard view for individual payment intents:

```text
GET /dashboard/payment-intents/{payment_intent_id}?token=...
```

The dashboard displays:

- payment intent details,
- status badge,
- amount and currency,
- reference,
- merchant ID,
- XRPL transaction hash,
- timestamps,
- recent webhook deliveries.

The dashboard is protected by `DASHBOARD_TOKEN`.

## Configuration

### WooCommerce gateway settings

The gateway supports:

- Enable / disable,
- Title,
- Description,
- EuroLedger API base URL,
- Merchant API key,
- Webhook secret,
- Dashboard base URL.

For local development, typical values are:

```text
EuroLedger API base URL:
http://euroledger-xrpl-backend:8000

Webhook URL registered in EuroLedger:
http://euroledger-wp-dev/?rest_route=/euroledger-xrpl/v1/webhook

Dashboard base URL:
http://localhost:8000/dashboard?token=dev-dashboard-token
```

### Backend settings

The backend dashboard requires:

```env
DASHBOARD_TOKEN=dev-dashboard-token
```

## Development validation

This release includes end-to-end smoke scripts for the WooCommerce integration:

```bash
export MERCHANT_API_KEY='...'

scripts/dev/woocommerce-smoke-e2e-confirmed.sh
scripts/dev/woocommerce-smoke-e2e-cancelled.sh
```

The confirmed smoke script validates:

```text
create WooCommerce order
→ create payment intent
→ confirm payment intent
→ deliver webhook
→ WooCommerce order becomes processing
```

The cancelled smoke script validates:

```text
create WooCommerce order
→ create payment intent
→ cancel payment intent
→ deliver webhook
→ WooCommerce order becomes cancelled
```

A helper is also available for creating test orders:

```bash
scripts/dev/woocommerce-create-test-order.sh
```

## Packaging

The plugin ZIP can be generated with:

```bash
scripts/dev/package-woocommerce-plugin.sh
```

Expected output:

```text
dist/euroledger-xrpl-gateway.zip
dist/euroledger-xrpl-gateway.zip.sha256
```

The package keeps the expected WordPress plugin directory structure:

```text
euroledger-xrpl-gateway/
euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
euroledger-xrpl-gateway/includes/...
```

## Versioning

The plugin version is managed with:

```bash
scripts/dev/set-woocommerce-plugin-version.sh 0.1.1
```

The workflow updates:

- the WordPress plugin header,
- the internal plugin version constant,
- the plugin README stable tag when present.

## Known limitations

- WooCommerce Checkout Blocks are not supported yet. Use classic checkout.
- The backend dashboard uses a simple token-based protection mechanism intended for development and early internal use.
- The dashboard link should only be enabled when a dashboard URL and token are configured.
- Webhook delivery depends on a reachable WordPress URL from the backend container.
- In local dev, the recommended webhook URL uses `rest_route` to avoid WordPress canonical redirect issues.
- Automatic refunds are not implemented.
- This release does not provide a public merchant portal or full dashboard authentication.
- Production hardening is still pending before real merchant deployment.

## Recommended release checklist

Before publishing or sharing the plugin ZIP:

1. Verify the repo is clean.
2. Run PHP syntax checks for plugin files.
3. Run backend tests if dashboard or API code changed.
4. Confirm the webhook endpoint is configured.
5. Run the confirmed WooCommerce smoke test.
6. Run the cancelled WooCommerce smoke test.
7. Review the WooCommerce orders list.
8. Review the WooCommerce order detail panel.
9. Review the customer order received / view order pages.
10. Review the backend dashboard page.
11. Generate the plugin ZIP.
12. Verify ZIP structure.
13. Store or publish the checksum.

## Suggested release note

EuroLedger XRPL WooCommerce Gateway v0.1.1 introduces the first complete development version of the WooCommerce payment integration. It supports classic checkout payment intent creation, signed webhook processing, automatic WooCommerce order updates, customer-facing payment status, admin order visibility, a backend payment intent dashboard, end-to-end smoke scripts, plugin packaging, and versioning workflows.

This version is suitable for local development and controlled internal testing. It is not yet intended as a hardened production release.
