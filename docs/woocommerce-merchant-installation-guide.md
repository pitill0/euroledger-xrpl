# EuroLedger XRPL WooCommerce Gateway — Merchant Installation Guide

This guide explains how to install and configure the EuroLedger XRPL WooCommerce Gateway plugin.

## Requirements

Before installing the plugin, make sure you have:

- A WordPress site with WooCommerce installed.
- The EuroLedger XRPL Gateway plugin ZIP.
- A EuroLedger merchant API key.
- A webhook secret.
- The EuroLedger API base URL.
- Access to the WordPress admin panel.

## 1. Install the plugin

In WordPress admin, go to:

```text
Plugins → Add New → Upload Plugin
```

Upload the plugin ZIP:

```text
euroledger-xrpl-gateway-0.1.3.zip
```

Then click:

```text
Install Now → Activate Plugin
```

## 2. Open the payment settings

Go to:

```text
WooCommerce → Settings → Payments
```

Enable:

```text
EuroLedger XRPL
```

Then open the EuroLedger XRPL settings.

You can also open the settings page directly:

```text
/wp-admin/admin.php?page=wc-settings&tab=checkout&section=euroledger_xrpl
```

## 3. Configure the gateway

Fill in the required fields:

```text
Enable gateway: Yes
API base URL: https://your-euroledger-api.example.com
Merchant API key: your merchant API key
Webhook secret: your webhook secret
Title: EuroLedger XRPL
Description: Pay securely using XRP Ledger through EuroLedger.
```

Save changes.

## 4. Configure the webhook in EuroLedger

In your EuroLedger merchant backend, configure the WooCommerce webhook endpoint.

The WooCommerce webhook endpoint is:

```text
https://your-store.example.com/wp-json/euroledger-xrpl/v1/webhook
```

Use the same webhook secret that you configured in WooCommerce.

## 5. Checkout page compatibility

The gateway supports both:

```text
Classic WooCommerce checkout
WooCommerce Checkout Blocks
```

### Classic checkout

The classic checkout page uses:

```text
[woocommerce_checkout]
```

### Checkout Blocks

A Checkout Block page uses:

```html
<!-- wp:woocommerce/checkout /-->
```

For best compatibility, test the checkout flow after changing checkout page type.

## 6. Test a payment

Create a test product or use an existing low-value product.

Then:

1. Add the product to the cart.
2. Go to checkout.
3. Select `EuroLedger XRPL`.
4. Place the order.
5. Confirm that the WooCommerce order is created as `on-hold`.
6. Confirm that the order contains a EuroLedger payment intent ID and reference.
7. Confirm the payment in EuroLedger.
8. Check that WooCommerce updates the order to `processing`.

## 7. Order metadata

After placing an order, the WooCommerce order should contain EuroLedger metadata such as:

```text
Payment intent ID
Payment reference
EuroLedger payment status
XRPL transaction hash
Last webhook event
Last webhook delivery ID
```

This information is visible in the WooCommerce order admin screen.

## 8. Troubleshooting

### EuroLedger does not appear at checkout

Check that:

- The gateway is enabled.
- The API base URL is configured.
- The merchant API key is configured.
- The webhook secret is configured.
- WooCommerce checkout pages are configured correctly.

### Order stays on-hold

This usually means WooCommerce created the order and EuroLedger created the payment intent, but the payment confirmation webhook has not updated the order yet.

Check:

- The EuroLedger webhook endpoint URL.
- The webhook secret.
- Backend webhook delivery logs.
- WooCommerce order notes.
- WordPress logs.

### Webhook fails

Confirm that the webhook secret in WooCommerce matches the webhook secret configured in EuroLedger.

Also check that your store can receive public HTTPS requests at:

```text
/wp-json/euroledger-xrpl/v1/webhook
```

### WooCommerce Admin looks stale or broken

Clear browser cache, cookies, and local storage for the store domain, then retry in a clean browser session.

## 9. Upgrade notes

Version `0.1.3` adds WooCommerce Checkout Blocks support.

No WooCommerce database migration is required.

Merchants using classic checkout can upgrade without changing their checkout page.

Merchants using Checkout Blocks should test the full checkout flow after upgrading.

## 10. Support checklist

When reporting an issue, include:

```text
Plugin version
WooCommerce version
WordPress version
Checkout type: classic or blocks
Order ID
EuroLedger payment intent ID
Webhook delivery ID, if available
Relevant WooCommerce order notes
Relevant WordPress/PHP logs
```

## Related documentation

- [WooCommerce integration README](../plugin-woocommerce/README.md)
- [Gateway plugin README](../plugin-woocommerce/euroledger-xrpl-gateway/README.md)
- [WooCommerce Checkout Blocks](woocommerce-checkout-blocks.md)
- [WooCommerce gateway 0.1.3 release notes](woocommerce-gateway-0.1.3.md)
