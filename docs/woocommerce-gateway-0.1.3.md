# EuroLedger XRPL WooCommerce Gateway 0.1.3

## Summary

Version 0.1.3 adds support for WooCommerce Checkout Blocks while preserving the existing classic checkout flow.

This release registers EuroLedger XRPL as a Blocks-compatible payment method and reuses the existing server-side gateway processing logic, so block checkout orders create EuroLedger payment intents and continue through the existing webhook confirmation flow.

## Changes

- Added WooCommerce Checkout Blocks payment method integration.
- Added Store API / Blocks registration for the `euroledger_xrpl` gateway.
- Added frontend Blocks checkout script.
- Reused the existing `process_payment()` flow for block checkout orders.
- Improved gateway configuration health checks.
- Fixed WooCommerce Blocks compatibility issues with inherited settings and helper method names.
- Documented Checkout Blocks development and validation flow.

## Validation

Validated manually in the local WooCommerce development environment:

- Classic checkout still works.
- Cart classic + Checkout Block works in browser.
- EuroLedger XRPL appears as an available Checkout Blocks payment method.
- Store API checkout creates a WooCommerce order.
- EuroLedger payment intent is created with status `pending`.
- Backend confirmation triggers merchant webhook delivery.
- WooCommerce order is updated to `processing`.
- EuroLedger order metadata is updated to `confirmed`.

## Known notes

During validation, one browser showed stale WooCommerce Admin and cart state due to local browser cache/cookies/local storage. Re-testing in a clean browser confirmed the Payments admin screen and checkout flow worked correctly.

## Upgrade notes

No database migration is required for the WooCommerce plugin.

Merchants using classic checkout can upgrade without changing checkout pages.

Merchants using Checkout Blocks should confirm that the EuroLedger gateway settings are complete:

- API base URL
- Merchant API key
- Webhook secret
- Gateway enabled

