# EuroLedger XRPL WooCommerce Integration

This directory contains the WooCommerce integration for EuroLedger XRPL.

The current gateway plugin lives under:

```text
plugin-woocommerce/euroledger-xrpl-gateway/
```

Current plugin version:

```text
0.1.3
```

## Purpose

The WooCommerce gateway lets a WooCommerce store create EuroLedger XRPL payment intents from WooCommerce orders.

It supports:

- Classic WooCommerce checkout.
- WooCommerce Checkout Blocks.
- EuroLedger payment intent creation.
- Merchant API key authentication.
- Webhook-based payment confirmation.
- WooCommerce order metadata updates.
- Admin order payment details.
- Customer-facing payment status.
- Local development, smoke testing, and packaging workflows.

## Directory map

```text
plugin-woocommerce/
├── README.md
├── dev/
│   ├── README.md
│   └── docker-compose.yml
└── euroledger-xrpl-gateway/
    ├── README.md
    ├── euroledger-xrpl-gateway.php
    ├── assets/js/blocks-checkout.js
    └── includes/
```

## Documentation roles

Use this section to choose the right document.

### Merchants

For store owners or operators installing the plugin:

- [Merchant installation guide](../docs/woocommerce-merchant-installation-guide.md)
- [Gateway plugin README](euroledger-xrpl-gateway/README.md)

### Plugin developers

For local development and gateway maintenance:

- [Gateway plugin README](euroledger-xrpl-gateway/README.md)
- [Local development environment](dev/README.md)
- [Webhook development flow](../docs/woocommerce-webhook-dev-flow.md)
- [Checkout Blocks support](../docs/woocommerce-checkout-blocks.md)
- [Smoke tests](../docs/woocommerce-smoke-tests.md)

### Release maintainers

For preparing and validating plugin releases:

- [Plugin packaging](../docs/woocommerce-plugin-packaging.md)
- [Plugin versioning](../docs/woocommerce-plugin-versioning.md)
- [Release checklist](../docs/woocommerce-plugin-release-checklist.md)
- [Configuration hardening](../docs/woocommerce-plugin-configuration-hardening.md)
- [0.1.3 release notes](../docs/woocommerce-gateway-0.1.3.md)
- [0.1.3 public release notes](../docs/releases/woocommerce-gateway-0.1.3-public.md)

## Checkout support

### Classic checkout

Classic checkout uses:

```text
[woocommerce_checkout]
```

Expected flow:

```text
WooCommerce order
→ EuroLedger payment intent
→ order on-hold
→ payment confirmation webhook
→ order processing
```

### Checkout Blocks

Checkout Blocks use:

```html
<!-- wp:woocommerce/checkout /-->
```

The plugin registers `euroledger_xrpl` as a Store API / Blocks-compatible payment method and reuses the existing server-side gateway payment flow.

Validated flow:

```text
Checkout Block
→ Store API checkout
→ WooCommerce order
→ EuroLedger payment intent
→ webhook confirmation
→ order processing
```

## Local development

Start the local WooCommerce development environment:

```bash
cd plugin-woocommerce/dev
sudo docker compose up -d
```

Check plugin status:

```bash
sudo docker compose --profile tools run --rm wp-cli wp plugin status euroledger-xrpl-gateway
```

Check gateway settings:

```bash
sudo docker compose --profile tools run --rm wp-cli wp option get \
  woocommerce_euroledger_xrpl_settings \
  --format=json | python -m json.tool
```

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

Use the development packaging script:

```bash
scripts/dev/package-woocommerce-plugin.sh
```

The generated ZIP should be named with the plugin version, for example:

```text
dist/euroledger-xrpl-gateway-0.1.3.zip
```

Before publishing, verify that the ZIP does not contain development-only files:

```bash
unzip -l dist/euroledger-xrpl-gateway-0.1.3.zip \
  | grep -Ei "dev/|\.git|node_modules|__MACOSX|\.DS_Store|\.env|pytest_cache|__pycache__"
```

The command should return no output.

## Notes

During local validation of version `0.1.3`, one browser showed stale WooCommerce Admin and cart state due to local cache, cookies, or local storage. Re-testing in a clean browser confirmed that WooCommerce Payments and the checkout flow worked correctly.

When debugging WooCommerce Admin or Checkout Blocks locally, use a clean browser session if REST, cart, or Store API state appears inconsistent.
