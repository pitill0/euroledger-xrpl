# WooCommerce smoke tests

These scripts exercise the EuroLedger WooCommerce integration against the local Docker development stack.

They are intentionally smoke tests, not full PHPUnit tests. Each script uses a real WooCommerce order, a real backend payment intent, the webhook delivery queue, and the WordPress receiver.

## Prerequisites

Start the backend stack and the WooCommerce dev stack. The WordPress container must be attached to the backend Docker network, as described in the WooCommerce dev flow docs.

Configure the gateway in WooCommerce with:

- API base URL: `http://euroledger-xrpl-backend:8000`
- Merchant API key: a valid merchant API key
- Webhook secret: the same secret configured in the backend webhook endpoint
- Webhook endpoint URL in backend: `http://euroledger-wp-dev/?rest_route=/euroledger-xrpl/v1/webhook`

Export the merchant API key before running the scripts:

```bash
export MERCHANT_API_KEY='your-dev-merchant-api-key'
```

## Confirmed payment flow

Create a new WooCommerce checkout order with the EuroLedger XRPL gateway. Leave it pending/on-hold.

Then run:

```bash
cd ~/projects/euroledger-xrpl
scripts/dev/woocommerce-smoke-confirmed.sh
```

The script discovers the latest pending EuroLedger order, confirms its payment intent in the backend, waits for the webhook delivery, and verifies that the WooCommerce order becomes `processing`.

Expected final checks:

```text
ORDER_STATUS=processing
EUROLEDGER_STATUS=confirmed
LAST_EVENT=payment_intent.confirmed
XRPL_HASH=<64-char hash>
```

You can also pass an explicit order and intent:

```bash
ORDER_ID=123 PAYMENT_INTENT_ID='...' scripts/dev/woocommerce-smoke-confirmed.sh
```

## Cancelled payment flow

Create a new WooCommerce checkout order with the EuroLedger XRPL gateway. Leave it pending/on-hold.

Then run:

```bash
cd ~/projects/euroledger-xrpl
scripts/dev/woocommerce-smoke-cancelled.sh
```

The script discovers the latest pending EuroLedger order, cancels its payment intent in the backend, waits for the webhook delivery, and verifies that the WooCommerce order becomes `cancelled`.

Expected final checks:

```text
ORDER_STATUS=cancelled
EUROLEDGER_STATUS=cancelled
LAST_EVENT=payment_intent.cancelled
CANCELLATION_REASON=Customer changed their mind
```

You can override the cancellation reason:

```bash
CANCELLATION_REASON='Customer requested cancellation' scripts/dev/woocommerce-smoke-cancelled.sh
```

You can also pass an explicit order and intent:

```bash
ORDER_ID=124 PAYMENT_INTENT_ID='...' scripts/dev/woocommerce-smoke-cancelled.sh
```

## Worker output

The scripts run the webhook worker once after changing the payment intent state. The command may report `processed=0` if the automatic webhook worker service already delivered the webhook first. That is acceptable as long as the delivery ends in `delivered` and the WooCommerce order status matches the expected final state.

## Useful environment variables

```bash
BACKEND_URL='http://localhost:8000'
WP_DEV_DIR='/path/to/euroledger-xrpl/plugin-woocommerce/dev'
DOCKER_COMPOSE='sudo docker compose'
MAX_WAIT_SECONDS=60
```

## Avoiding stale shell variables

If you previously exported `ORDER_ID` or `PAYMENT_INTENT_ID`, unset them before running discovery mode:

```bash
unset ORDER_ID PAYMENT_INTENT_ID
```

When no explicit IDs are provided, the scripts now discover candidate WooCommerce orders and verify the backend payment intent is still `pending` before using it. This avoids stale WordPress metadata from older orders whose backend intent was already confirmed, cancelled, or expired.
