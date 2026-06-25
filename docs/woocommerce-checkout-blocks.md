# WooCommerce Checkout Blocks support

EuroLedger XRPL Gateway supports the WooCommerce classic checkout and registers a minimal payment method integration for WooCommerce Checkout Blocks.

## Scope

The Blocks integration exposes the same `euroledger_xrpl` payment method used by the classic gateway. It reuses the existing WooCommerce gateway configuration and server-side `process_payment()` flow.

Supported behavior:

- EuroLedger XRPL appears as a payment method in Checkout Blocks when the gateway is enabled and checkout-ready.
- The Blocks payment method uses the configured gateway title and description.
- Checkout submission uses the existing WooCommerce gateway payment processing path.
- Backend payment intent creation, webhook processing, admin metadata, customer status and dashboard links remain shared with the classic checkout flow.

## Configuration readiness

The Blocks payment method is only active when the same required configuration is present:

1. API base URL;
2. merchant API key;
3. webhook secret.

If any required setting is missing, the method is hidden from Checkout Blocks, matching classic checkout behavior.

## Files

```text
plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-blocks-payment-method.php
plugin-woocommerce/euroledger-xrpl-gateway/assets/js/blocks-checkout.js
```

The PHP integration registers the payment method with WooCommerce Blocks. The JavaScript file registers the frontend payment method using WooCommerce Blocks registry APIs.

## Local validation

1. Configure the gateway health checks until checkout-ready.
2. Set the WooCommerce checkout page to a Checkout Block page.
3. Open checkout and verify **EuroLedger XRPL** appears as a payment method.
4. Place an order.
5. Verify a backend payment intent is created.
6. Verify the order is `on-hold` and contains EuroLedger metadata.
7. Confirm or cancel the payment intent.
8. Verify signed webhook delivery updates the WooCommerce order.

## Known limitations

- The frontend Blocks UI is intentionally minimal in this release.
- The payment method does not collect additional fields in the block checkout.
- The full smoke scripts still target the classic checkout/helper flow, not a browser-driven Blocks checkout session.
