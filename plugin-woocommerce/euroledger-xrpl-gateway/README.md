# EuroLedger XRPL WooCommerce Gateway

Experimental WooCommerce payment gateway for EuroLedger XRPL.

This first block only provides the installable plugin skeleton and gateway
settings. It does not create backend payment intents during checkout yet.

## Current Scope

- Registers a WooCommerce payment gateway.
- Adds admin settings for:
  - enable/disable;
  - checkout title;
  - checkout description;
  - EuroLedger backend API base URL;
  - merchant API key;
  - test mode;
  - debug logging.
- Keeps the gateway disabled by default.
- Fails checkout explicitly until backend payment intent creation is added.

## Install Locally

Copy or symlink this folder into WordPress:

```text
wp-content/plugins/euroledger-xrpl-gateway
```

Then activate:

```bash
wp plugin activate euroledger-xrpl-gateway
```

Or activate it from the WordPress admin plugins screen.

## Configure

Open:

```text
WooCommerce > Settings > Payments > EuroLedger XRPL
```

Set:

```text
API base URL: http://localhost:8000
Merchant API key: <merchant-api-key>
Test mode: enabled
```

Do not enable the gateway for real checkout until payment intent creation is
implemented.

## Next Integration Block

The next block should:

1. create a backend payment intent from the WooCommerce order;
2. persist the payment intent id/reference in order metadata;
3. redirect the customer to an order payment instructions page;
4. keep the order in `pending` or `on-hold`;
5. add tests or manual validation around duplicate checkout submission.
