# WooCommerce Gateway 0.1.3

EuroLedger XRPL WooCommerce Gateway `0.1.3` adds support for WooCommerce Checkout Blocks while keeping the existing classic checkout flow unchanged.

## Highlights

- WooCommerce Checkout Blocks support.
- Classic WooCommerce checkout remains supported.
- EuroLedger XRPL is registered as a Store API / Blocks-compatible payment method.
- Block-based checkout orders reuse the existing server-side gateway flow.
- Payment intent creation remains handled by the EuroLedger XRPL backend.
- Merchant webhook confirmation updates WooCommerce orders automatically.
- End-to-end flow validated locally:
  - order creation
  - payment intent creation
  - backend payment confirmation
  - webhook delivery
  - WooCommerce order transition to `processing`

## Assets

Attach these files to the release:

```text
euroledger-xrpl-gateway-0.1.3.zip
euroledger-xrpl-gateway-0.1.3.zip.sha256
```

## Upgrade notes

No WooCommerce database migration is required.

Merchants using classic checkout can upgrade without changing their checkout page.

Merchants using WooCommerce Checkout Blocks should verify that the EuroLedger XRPL gateway settings are complete:

- API base URL
- Merchant API key
- Webhook secret
- Gateway enabled

After upgrading, merchants should place a low-value test order and confirm that the WooCommerce order moves from `on-hold` to `processing` after payment confirmation.

## Validation summary

This release was validated in the local WooCommerce development environment using:

- Classic checkout.
- Classic cart plus Checkout Block.
- WooCommerce Store API checkout.
- Backend payment intent confirmation.
- Merchant webhook delivery.
- WooCommerce order metadata updates.

## Known notes

During local validation, one browser showed stale WooCommerce Admin and cart state due to local cache, cookies, or local storage.

Re-testing in a clean browser confirmed that the WooCommerce Payments admin screen and checkout flow worked correctly.

When testing WooCommerce Admin or Checkout Blocks locally, use a clean browser session if REST, cart, or Store API state appears inconsistent.
