# WooCommerce Plugin Release Checklist

This checklist is intended for local development releases of the experimental
EuroLedger XRPL WooCommerce gateway.

The plugin is testnet-first and must not be treated as production payment
software. Use this checklist before creating a distributable plugin ZIP or before
sharing a build for manual testing.

## 1. Repository state

Start from a clean working tree.

```bash
git status --short
git log --oneline -8
```

Do not include unrelated changes in a plugin release commit or package.

## 2. PHP syntax checks

Run syntax checks for the plugin entrypoint and all PHP classes.

```bash
php -l plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-api-client.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-webhook-receiver.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-admin-order-meta.php
```

## 3. Backend checks when API, webhooks or dashboard changed

If the change touches backend API routes, webhook delivery, dashboard rendering,
configuration or repositories, run the relevant backend checks inside the backend
container.

```bash
sudo docker compose exec backend pytest
sudo docker compose exec backend ruff check app tests
sudo docker compose exec backend ruff format --check app tests
```

For dashboard-only changes, at minimum run:

```bash
sudo docker compose exec backend pytest tests/test_dashboard.py tests/test_settings.py
```

## 4. Local environment sanity check

Ensure the backend and WooCommerce dev environment are running.

```bash
cd ~/projects/euroledger-xrpl
sudo docker compose ps

cd ~/projects/euroledger-xrpl/plugin-woocommerce/dev
sudo docker compose ps
```

Confirm that the WooCommerce dev container can reach the backend using the
internal backend URL configured in the gateway settings.

```text
http://euroledger-xrpl-backend:8000
```

## 5. Webhook endpoint

For local dev, the recommended WooCommerce receiver URL is:

```text
http://euroledger-wp-dev/?rest_route=/euroledger-xrpl/v1/webhook
```

Check that a merchant webhook endpoint exists and uses the same secret as the
WooCommerce gateway setting.

```bash
curl -s http://localhost:8000/webhook-endpoints \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

If needed, recreate it:

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

## 6. Confirmed payment smoke test

Run the one-command confirmed flow.

```bash
cd ~/projects/euroledger-xrpl
export MERCHANT_API_KEY='YOUR_DEV_MERCHANT_API_KEY'

scripts/dev/woocommerce-smoke-e2e-confirmed.sh
```

Expected result:

```text
WooCommerce order status: processing
EuroLedger status: confirmed
Webhook event: payment_intent.confirmed
Webhook delivery: delivered
```

## 7. Cancelled payment smoke test

Run the one-command cancelled flow.

```bash
cd ~/projects/euroledger-xrpl
export MERCHANT_API_KEY='YOUR_DEV_MERCHANT_API_KEY'

scripts/dev/woocommerce-smoke-e2e-cancelled.sh
```

Expected result:

```text
WooCommerce order status: cancelled
EuroLedger status: cancelled
Webhook event: payment_intent.cancelled
Webhook delivery: delivered
```

## 8. Admin UI checks

Open WooCommerce admin and verify:

```text
WooCommerce > Orders
```

Check that the orders list shows the `EuroLedger` column with the expected badge,
reference and optional dashboard link.

Then open at least one confirmed order and one cancelled order. Verify the
EuroLedger admin panel shows:

```text
Payment reference
Payment intent ID
EuroLedger status badge
XRPL transaction hash when confirmed
Cancellation reason when cancelled
Last webhook event
Last webhook delivery ID
Dashboard link when configured
```

## 9. Customer UI checks

Open the order received URL or the customer view order URL for recent test orders.

Verify that the customer-facing EuroLedger block shows:

```text
pending / confirmed / cancelled / expired status
payment reference
payment intent ID
XRPL transaction hash when confirmed
cancellation reason when cancelled
```

## 10. Backend dashboard check

If `Dashboard base URL` is configured in WooCommerce, click `View in EuroLedger`
from an admin order screen.

Expected result:

```text
/dashboard/payment-intents/{payment_intent_id}?token=...
```

The page should render an HTML dashboard with the payment intent details and
recent webhook deliveries.

## 11. Package the plugin

Generate a distributable plugin ZIP.

```bash
cd ~/projects/euroledger-xrpl
scripts/dev/package-woocommerce-plugin.sh
```

Expected files:

```text
dist/euroledger-xrpl-gateway.zip
dist/euroledger-xrpl-gateway.zip.sha256
```

Inspect the package structure:

```bash
unzip -l dist/euroledger-xrpl-gateway.zip | head -40
```

The ZIP should contain the plugin directory as its root entry:

```text
euroledger-xrpl-gateway/
euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
euroledger-xrpl-gateway/includes/...
```

## 12. Optional install test

Install the generated ZIP in a clean WordPress/WooCommerce dev environment and
repeat the confirmed and cancelled smoke tests.

## 13. Final git checks

Before committing or tagging:

```bash
git status --short
git diff --check -- .
```

A release-related commit should not include generated files from `dist/` unless
there is an explicit decision to version release artifacts.

## 14. Release notes draft

For each release, capture a short summary:

```text
Version:
Date:
Commit:
Package:
Checksum:
Validated flows:
- confirmed smoke test:
- cancelled smoke test:
- admin order panel:
- orders list:
- customer order page:
- backend dashboard:
Known limitations:
```

## Known limitations

The WooCommerce gateway is still experimental and testnet-first.

Classic checkout remains the primary smoke-tested path. WooCommerce Checkout Blocks support is available as a minimal integration and should be checked manually when a release changes checkout behavior.

The backend dashboard token is a dev-oriented protection mechanism. A production
dashboard would need a stronger authentication and authorization model.

## Configuration health

Before packaging, open `WooCommerce > Settings > Payments > EuroLedger XRPL` and confirm the **Configuration health** panel has no blocking errors. Confirm **Dashboard base URL** points to the HTML dashboard route, not the raw backend API root.
