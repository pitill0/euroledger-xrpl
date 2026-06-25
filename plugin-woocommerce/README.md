# EuroLedger XRPL WooCommerce Integration

This directory contains the WooCommerce integration for the EuroLedger XRPL project.

The current gateway plugin lives under:

```text
plugin-woocommerce/euroledger-xrpl-gateway/
```

## Current version

`0.1.3`

## What is included

The WooCommerce gateway allows stores to accept EuroLedger XRPL payments by connecting WooCommerce orders with the EuroLedger XRPL backend.

It supports:

- Classic WooCommerce checkout.
- WooCommerce Checkout Blocks.
- EuroLedger payment intent creation.
- Merchant API key authentication.
- Webhook-based payment confirmation.
- WooCommerce order metadata updates.
- Admin order payment details.
- Customer-facing payment status.
- Local development tooling.
- Smoke and end-to-end validation scripts.
- Plugin packaging workflow.

## Plugin

Main plugin path:

```text
plugin-woocommerce/euroledger-xrpl-gateway/
```

Main plugin file:

```text
plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
```

Plugin README:

```text
plugin-woocommerce/euroledger-xrpl-gateway/README.md
```

## Local development environment

A local WooCommerce development environment is available under:

```text
plugin-woocommerce/dev/
```

Start the environment:

```bash
cd plugin-woocommerce/dev
sudo docker compose up -d
```

Use WP-CLI:

```bash
sudo docker compose --profile tools run --rm wp-cli wp plugin status euroledger-xrpl-gateway
```

Check gateway settings:

```bash
sudo docker compose --profile tools run --rm wp-cli wp option get \
  woocommerce_euroledger_xrpl_settings \
  --format=json | python -m json.tool
```

## Checkout support

### Classic checkout

The gateway supports the classic WooCommerce checkout shortcode:

```text
[woocommerce_checkout]
```

Classic checkout validation should confirm:

- The EuroLedger XRPL method appears.
- WooCommerce creates an order.
- The gateway creates a EuroLedger payment intent.
- The order starts as `on-hold`.
- Webhook confirmation moves the order to `processing`.

### Checkout Blocks

Since version `0.1.3`, the gateway supports WooCommerce Checkout Blocks.

A Checkout Block page can use:

```html
<!-- wp:woocommerce/checkout /-->
```

The gateway registers `euroledger_xrpl` as a Blocks-compatible payment method and reuses the existing server-side payment flow.

Validated Checkout Blocks flow:

- Store API exposes `euroledger_xrpl` as an available payment method.
- Checkout Block can create a WooCommerce order.
- A EuroLedger payment intent is created.
- The order starts as `on-hold`.
- Backend confirmation triggers webhook delivery.
- WooCommerce updates the order to `processing`.

## Validation

From the repository root:

```bash
php -l plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-blocks-payment-method.php
node --check plugin-woocommerce/euroledger-xrpl-gateway/assets/js/blocks-checkout.js
git diff --check -- plugin-woocommerce docs
```

## Packaging

Use the repository packaging script to build a distributable plugin ZIP.

Find available packaging scripts:

```bash
find . -maxdepth 3 -type f \
  \( -name "*package*" -o -name "*release*" \) \
  | sort
```

After creating the ZIP, inspect it before publishing:

```bash
unzip -l path/to/euroledger-xrpl-gateway.zip | head -80

unzip -l path/to/euroledger-xrpl-gateway.zip | grep -Ei "dev/|\.git|node_modules|__MACOSX|\.DS_Store|\.env"
```

The second command should return no output.

## Release notes

### 0.1.3

- Add WooCommerce Checkout Blocks support.
- Register EuroLedger XRPL as a Store API / Blocks-compatible payment method.
- Reuse the existing classic gateway payment flow for block-based checkout orders.
- Validate end-to-end block checkout flow with webhook confirmation.
- Fix WooCommerce Blocks compatibility issues found during local validation.
- Improve gateway configuration health checks.

### 0.1.2

- Add gateway configuration health checks.
- Improve admin notices for incomplete gateway configuration.
- Document release and upgrade workflow.

### 0.1.1

- Add release documentation.
- Add webhook development documentation.
- Add smoke test and packaging workflow documentation.

### 0.1.0

- Initial WooCommerce gateway implementation.
- Create EuroLedger payment intents from WooCommerce orders.
- Store EuroLedger metadata on WooCommerce orders.
- Receive and validate EuroLedger webhook events.
- Update WooCommerce order status after payment confirmation.

## Notes

During local validation of `0.1.3`, one browser showed stale WooCommerce Admin and cart state caused by local cache, cookies, or local storage. Re-testing in a clean browser confirmed that WooCommerce Payments and the checkout flow worked correctly.

When debugging WooCommerce Admin or Checkout Blocks locally, use a clean browser session if REST, cart, or Store API state appears inconsistent.
