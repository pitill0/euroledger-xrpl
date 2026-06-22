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
move confirmed orders to processing.
