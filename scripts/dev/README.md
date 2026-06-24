# Dev scripts

## WooCommerce smoke tests

Run these scripts from the repository root after creating a new pending EuroLedger WooCommerce order.

```bash
export MERCHANT_API_KEY='your-dev-merchant-api-key'
unset ORDER_ID PAYMENT_INTENT_ID

scripts/dev/woocommerce-smoke-confirmed.sh
scripts/dev/woocommerce-smoke-cancelled.sh
```

If you pass explicit IDs, pass both values together:

```bash
ORDER_ID=123 PAYMENT_INTENT_ID='...' scripts/dev/woocommerce-smoke-confirmed.sh
```

The scripts skip stale WooCommerce orders whose backend payment intent is no longer `pending`.

See `docs/woocommerce-smoke-tests.md` for the full flow and troubleshooting notes.
