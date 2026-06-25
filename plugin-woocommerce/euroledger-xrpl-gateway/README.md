# EuroLedger XRPL Gateway for WooCommerce

EuroLedger XRPL Gateway adds XRP Ledger payment support to WooCommerce stores through the EuroLedger XRPL backend.

The gateway creates EuroLedger payment intents from WooCommerce orders, stores the payment reference on the order, and updates the order automatically when EuroLedger delivers payment confirmation webhooks.

Current version:

```text
0.1.3
```

## Features

- WooCommerce payment gateway for EuroLedger XRPL.
- Classic WooCommerce checkout support.
- WooCommerce Checkout Blocks support.
- EuroLedger payment intent creation from WooCommerce orders.
- Merchant API key authentication.
- Webhook receiver with HMAC signature validation.
- Automatic WooCommerce order updates from EuroLedger webhooks.
- Admin order metadata panel with EuroLedger payment details.
- EuroLedger status column in WooCommerce orders list.
- Customer-facing order status information.
- Gateway configuration health checks.
- Local development and smoke test tooling.

## Requirements

- WordPress with WooCommerce installed and active.
- PHP compatible with the WooCommerce environment.
- A running EuroLedger XRPL backend.
- A valid EuroLedger merchant API key.
- A webhook secret configured both in EuroLedger and WooCommerce.
- WooCommerce checkout pages configured.

## Installation

Copy the plugin directory into the WordPress plugins folder:

```text
wp-content/plugins/euroledger-xrpl-gateway/
```

Then activate the plugin from the WordPress admin panel or with WP-CLI:

```bash
wp plugin activate euroledger-xrpl-gateway
```

For merchant-oriented installation instructions, see:

```text
docs/woocommerce-merchant-installation-guide.md
```

## Configuration

Open the EuroLedger XRPL gateway settings from WooCommerce:

```text
WooCommerce → Settings → Payments → EuroLedger XRPL
```

Direct settings URL:

```text
/wp-admin/admin.php?page=wc-settings&tab=checkout&section=euroledger_xrpl
```

Configure:

- Enable gateway.
- API base URL.
- Merchant API key.
- Webhook secret.
- Gateway title.
- Gateway description.

The gateway health checks show admin notices when required configuration values are missing or invalid.

## Checkout support

### Classic checkout

The plugin supports the classic WooCommerce checkout shortcode:

```text
[woocommerce_checkout]
```

When a customer places an order using EuroLedger XRPL:

1. WooCommerce creates the order.
2. The gateway creates a EuroLedger payment intent.
3. The order is moved to `on-hold`.
4. EuroLedger payment metadata is stored on the order.
5. The customer is redirected to the order received page.

### Checkout Blocks

Since version `0.1.3`, the plugin supports WooCommerce Checkout Blocks.

A Checkout Block page can use:

```html
<!-- wp:woocommerce/checkout /-->
```

The gateway registers `euroledger_xrpl` as a Blocks-compatible payment method and reuses the existing server-side WooCommerce gateway flow.

Validated flow:

```text
Checkout Block
→ Store API checkout
→ WooCommerce order
→ EuroLedger payment intent
→ order on-hold
→ webhook confirmation
→ order processing
```

## Webhooks

EuroLedger sends merchant webhook events to WooCommerce when a payment intent changes state.

The WooCommerce webhook endpoint validates the webhook signature using the configured webhook secret before updating orders.

Expected confirmed payment flow:

```text
payment_intent.created
payment_intent.confirmed
```

When a payment intent is confirmed:

- WooCommerce order status changes to `processing`.
- EuroLedger metadata is updated.
- XRPL transaction hash is stored on the order.
- Last webhook event and delivery ID are stored for traceability.

## Order metadata

The plugin stores EuroLedger metadata on WooCommerce orders:

```text
_euroledger_payment_intent_id
_euroledger_payment_intent_reference
_euroledger_payment_intent_status
_euroledger_xrpl_transaction_hash
_euroledger_webhook_last_event
_euroledger_webhook_last_delivery_id
```

This metadata is shown in the WooCommerce admin order screen.

## Local development

The repository includes a local WooCommerce development environment under:

```text
plugin-woocommerce/dev/
```

Common commands:

```bash
cd plugin-woocommerce/dev

sudo docker compose up -d

sudo docker compose --profile tools run --rm wp-cli wp plugin status euroledger-xrpl-gateway
```

Check gateway settings:

```bash
sudo docker compose --profile tools run --rm wp-cli wp option get \
  woocommerce_euroledger_xrpl_settings \
  --format=json | python -m json.tool
```

## Manual validation

### Syntax checks

From the repository root:

```bash
php -l plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-blocks-payment-method.php
node --check plugin-woocommerce/euroledger-xrpl-gateway/assets/js/blocks-checkout.js
git diff --check -- plugin-woocommerce docs
```

### Classic checkout smoke test

1. Add a test product to the cart.
2. Open the classic checkout page.
3. Select EuroLedger XRPL.
4. Place the order.
5. Confirm that the order is `on-hold`.
6. Confirm that a EuroLedger payment intent was created.
7. Confirm the payment intent through the EuroLedger backend.
8. Confirm that the webhook updates the WooCommerce order to `processing`.

### Checkout Blocks smoke test

1. Use a classic cart page or another valid cart flow.
2. Open a Checkout Block page.
3. Confirm that EuroLedger XRPL appears as a payment method.
4. Place the order.
5. Confirm that the order is `on-hold`.
6. Confirm that a EuroLedger payment intent was created.
7. Confirm the payment intent through the EuroLedger backend.
8. Confirm that the webhook updates the WooCommerce order to `processing`.

## Release documentation

Detailed release and maintenance documents live in the repository `docs/` directory:

```text
docs/woocommerce-gateway-0.1.3.md
docs/releases/woocommerce-gateway-0.1.3-public.md
docs/woocommerce-plugin-packaging.md
docs/woocommerce-plugin-release-checklist.md
docs/woocommerce-plugin-versioning.md
docs/woocommerce-plugin-configuration-hardening.md
```

## Release notes

### 0.1.3

- Add support for WooCommerce Checkout Blocks.
- Register EuroLedger XRPL as a Store API / Blocks-compatible payment method.
- Reuse the existing classic gateway payment flow for block-based checkout orders.
- Improve gateway configuration health checks in the WooCommerce admin.
- Fix compatibility issues with WooCommerce Blocks inherited properties and methods.
- Validate end-to-end Checkout Blocks flow: order creation, payment intent creation, webhook confirmation, and WooCommerce order transition to `processing`.

### 0.1.2

- Add gateway configuration health checks.
- Improve admin visibility for incomplete or invalid configuration.
- Document release and upgrade workflow.

### 0.1.1

- Add initial WooCommerce gateway release documentation.
- Add webhook handling documentation.
- Add smoke test and packaging workflow documentation.

### 0.1.0

- Initial WooCommerce gateway implementation.
- Create EuroLedger payment intents from WooCommerce orders.
- Store EuroLedger metadata on orders.
- Receive and validate EuroLedger webhooks.
- Update WooCommerce orders from payment confirmation events.

## Known development notes

During local validation of `0.1.3`, one browser showed stale WooCommerce Admin and cart state caused by local browser cache, cookies, or local storage. Re-testing in a clean browser confirmed that the WooCommerce Payments screen and checkout flow worked correctly.

When debugging WooCommerce Blocks locally, use a clean browser session if the Store API, cart, or WooCommerce Admin screens appear inconsistent.

## License

This plugin is distributed as part of the EuroLedger XRPL project.

See the repository license for details.
