# WooCommerce Plugins

This folder contains experimental WooCommerce integrations for EuroLedger XRPL.

Current plugin:

```text
euroledger-xrpl-gateway/
```

The gateway is intentionally testnet-first and should not be used for real
payments.

## Local Development

A local WordPress/WooCommerce environment is available in `dev/`.

```bash
cd plugin-woocommerce/dev
sudo docker compose up -d
```

## Current Gateway Capabilities

The experimental gateway can check backend connectivity, create backend payment
intents during checkout and keep WooCommerce orders on hold while payment
confirmation is still pending. It can also receive signed backend webhooks to
move confirmed orders to processing and cancel on-hold orders when intents expire or are cancelled.

## Webhook Dev Flow

The local end-to-end webhook flow is documented in:

```text
../docs/woocommerce-webhook-dev-flow.md
```

That guide covers the classic checkout requirement, the backend and WordPress
container URLs, the local `rest_route` webhook URL, payment intent confirmation,
delivery inspection and the case where the automatic webhook worker processes a
delivery before a manual worker run.

## Admin order metadata

The gateway displays EuroLedger payment intent and webhook metadata on
WooCommerce order edit screens for orders paid with EuroLedger XRPL. It also
adds a compact **EuroLedger** column to WooCommerce order lists with the current
payment status, reference and an optional dashboard link. The admin panel
includes status badges, copy actions for operational identifiers and an optional
link to the EuroLedger payment intent dashboard when configured. See
`../docs/payment-intent-dashboard.md` for the backend route and token setup.
