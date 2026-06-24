# Dev scripts

## Create a WooCommerce smoke test order

Use this helper to create a real WooCommerce order through the EuroLedger XRPL gateway without using the browser.

```bash
cd ~/projects/euroledger-xrpl
scripts/dev/woocommerce-create-test-order.sh
```

It prints values that can be reused by the smoke tests:

```text
ORDER_ID=...
PAYMENT_INTENT_ID=...
REFERENCE=...
EUROLEDGER_STATUS=pending
ORDER_RECEIVED_URL=...
```

Optional variables:

```bash
SMOKE_PRODUCT_PRICE=5.00
SMOKE_CURRENCY=EUR
SMOKE_CUSTOMER_EMAIL=smoke-test@example.test
SMOKE_PRODUCT_SKU=euroledger-smoke-test-product
```

## WooCommerce smoke tests

Run these scripts from the repository root after creating a new pending EuroLedger WooCommerce order.

```bash
export MERCHANT_API_KEY='your-dev-merchant-api-key'
unset ORDER_ID PAYMENT_INTENT_ID

scripts/dev/woocommerce-smoke-confirmed.sh
scripts/dev/woocommerce-smoke-cancelled.sh
```

A fully scripted confirmed flow looks like this:

```bash
export MERCHANT_API_KEY='your-dev-merchant-api-key'
eval "$(scripts/dev/woocommerce-create-test-order.sh | tee /dev/stderr | grep -E '^(ORDER_ID|PAYMENT_INTENT_ID)=')"
scripts/dev/woocommerce-smoke-confirmed.sh
```

For cancellation, create a second fresh order:

```bash
export MERCHANT_API_KEY='your-dev-merchant-api-key'
eval "$(scripts/dev/woocommerce-create-test-order.sh | tee /dev/stderr | grep -E '^(ORDER_ID|PAYMENT_INTENT_ID)=')"
scripts/dev/woocommerce-smoke-cancelled.sh
```

If you pass explicit IDs, pass both values together:

```bash
ORDER_ID=123 PAYMENT_INTENT_ID='...' scripts/dev/woocommerce-smoke-confirmed.sh
```

The scripts skip stale WooCommerce orders whose backend payment intent is no longer `pending`.

See `docs/woocommerce-smoke-tests.md` for the full flow and troubleshooting notes.
