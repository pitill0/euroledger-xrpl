# WooCommerce Webhook Dev Flow

This document describes the local end-to-end flow for the experimental
EuroLedger XRPL WooCommerce gateway.

The goal is to validate this sequence in development:

```text
WooCommerce checkout
-> backend payment intent pending
-> backend payment intent confirmed
-> merchant webhook delivery
-> WordPress receiver
-> WooCommerce order processing
```

This flow is testnet-first and must not be used for real payments.

## Preconditions

Start the EuroLedger backend stack from the repository root:

```bash
cd ~/projects/euroledger-xrpl
sudo docker compose up -d
```

Start the WooCommerce dev stack:

```bash
cd ~/projects/euroledger-xrpl/plugin-woocommerce/dev
sudo docker compose up -d
```

The WooCommerce dev compose file connects WordPress and WP-CLI to the backend
compose network through the external `euroledger-xrpl_default` network. This lets
WordPress reach the backend by service name and lets the backend reach WordPress
by container name.

## Gateway Settings

Open the gateway settings in WordPress:

```text
WooCommerce > Settings > Payments > EuroLedger XRPL
```

Use these local values:

```text
API base URL: http://euroledger-xrpl-backend:8000
Merchant API key: <merchant-api-key>
Webhook secret: test-secret-123456789
Test mode: enabled
```

Use **Check backend connection** to verify the backend health endpoint and the
merchant API key before testing checkout.

## Classic Checkout Requirement

The current gateway implements the classic WooCommerce payment gateway flow. It
does not yet register a WooCommerce Blocks payment method.

For local testing, use classic checkout pages:

```bash
cd ~/projects/euroledger-xrpl/plugin-woocommerce/dev

CHECKOUT_ID=$(
  sudo docker compose --profile tools run --rm wp-cli wp post create \
    --post_type=page \
    --post_title="Checkout Classic" \
    --post_status=publish \
    --post_content="[woocommerce_checkout]" \
    --porcelain
)

sudo docker compose --profile tools run --rm wp-cli wp option update \
  woocommerce_checkout_page_id "$CHECKOUT_ID"

CART_ID=$(
  sudo docker compose --profile tools run --rm wp-cli wp post create \
    --post_type=page \
    --post_title="Cart Classic" \
    --post_status=publish \
    --post_content="[woocommerce_cart]" \
    --porcelain
)

sudo docker compose --profile tools run --rm wp-cli wp option update \
  woocommerce_cart_page_id "$CART_ID"
```

## Webhook Endpoint URL

In the local dev environment, prefer the WordPress `rest_route` form:

```text
http://euroledger-wp-dev/?rest_route=/euroledger-xrpl/v1/webhook
```

Avoid using `/wp-json/euroledger-xrpl/v1/webhook` for this dev setup when it
produces redirects or HTML responses. Signed webhooks should be sent directly to
the REST receiver without canonical redirects.

Create the backend webhook endpoint from the repository root:

```bash
cd ~/projects/euroledger-xrpl

export MERCHANT_API_KEY='<merchant-api-key>'

curl -s -X POST http://localhost:8000/webhook-endpoints \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://euroledger-wp-dev/?rest_route=/euroledger-xrpl/v1/webhook",
    "secret": "test-secret-123456789",
    "enabled": true
  }' | python -m json.tool
```

Confirm the endpoint exists:

```bash
curl -s http://localhost:8000/webhook-endpoints \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

## Receiver Smoke Test

Before creating an order, verify that the backend container reaches the
WordPress receiver. This unsigned request should fail with a JSON `401` response
from the plugin, not with HTML and not with a WordPress fatal error:

```bash
cd ~/projects/euroledger-xrpl

sudo docker compose exec -T backend python - <<'PY'
from urllib.error import HTTPError
from urllib.request import Request, urlopen

url = "http://euroledger-wp-dev/?rest_route=/euroledger-xrpl/v1/webhook"
request = Request(url, data=b"{}", method="POST")
request.add_header("Content-Type", "application/json")

try:
    with urlopen(request, timeout=10) as response:
        print(response.status)
        print(response.read(500).decode("utf-8", errors="replace"))
except HTTPError as exc:
    print(exc.code)
    print(exc.read(500).decode("utf-8", errors="replace"))
PY
```

Expected shape:

```text
401
{"code":"euroledger_missing_webhook_signature_headers", ...}
```

## E2E Test Order

Create a new WooCommerce order through the classic checkout and select
EuroLedger XRPL as the payment method. The order received page should show a
customer-facing **EuroLedger XRPL payment** block with a pending status badge,
payment reference and payment intent id.

Fetch the latest EuroLedger WooCommerce order from the dev stack:

```bash
cd ~/projects/euroledger-xrpl/plugin-woocommerce/dev

sudo docker compose --profile tools run --rm wp-cli wp eval '
$order = wc_get_orders([
    "limit" => 1,
    "orderby" => "date",
    "order" => "DESC",
    "payment_method" => "euroledger_xrpl",
])[0];

echo "ORDER_ID=" . $order->get_id() . PHP_EOL;
echo "STATUS=" . $order->get_status() . PHP_EOL;
echo "PAYMENT_INTENT_ID=" . $order->get_meta("_euroledger_payment_intent_id") . PHP_EOL;
echo "REFERENCE=" . $order->get_meta("_euroledger_payment_intent_reference") . PHP_EOL;
echo "INTENT_STATUS=" . $order->get_meta("_euroledger_payment_intent_status") . PHP_EOL;
'
```

The order should be `on-hold` and the stored intent status should be `pending`.
The same payment status block should also appear from **My account > Orders >
View order** for the customer.

## Confirm the Payment Intent

Confirm the new payment intent before it expires:

```bash
cd ~/projects/euroledger-xrpl

export MERCHANT_API_KEY='<merchant-api-key>'
export PAYMENT_INTENT_ID='<payment-intent-id>'

XRPL_HASH=$(
  python - <<'PY'
print("d" * 64)
PY
)

curl -s -X POST "http://localhost:8000/payment-intents/${PAYMENT_INTENT_ID}/confirm" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"xrpl_transaction_hash\":\"${XRPL_HASH}\"}" \
  | python -m json.tool
```

The response should show:

```text
"status": "confirmed"
```

## Verify Webhook Delivery

After confirmation, a `payment_intent.confirmed` delivery should exist:

```bash
curl -s "http://localhost:8000/webhook-deliveries?payment_intent_id=${PAYMENT_INTENT_ID}" \
  -H "X-API-Key: ${MERCHANT_API_KEY}" \
  | python -m json.tool
```

If the automatic webhook worker service is running, it may process the delivery
before a manual worker command is executed. In that case a manual run can report
all counters as zero because there are no due pending deliveries left in that
specific execution.

To process pending deliveries manually from the backend compose project:

```bash
cd ~/projects/euroledger-xrpl

sudo docker compose exec backend python -m app.commands.webhook_worker \
  --limit 100 \
  --timeout 10 \
  --max-attempts 5
```

A delivered webhook should look like:

```text
"status": "delivered"
"attempt_count": 1
"response_status_code": 200
"response_body": "{\"ok\":true,\"order_id\":19,\"status\":\"processing\"}"
```

## Verify the WooCommerce Order

Inspect the order metadata from the WooCommerce dev compose project:

```bash
cd ~/projects/euroledger-xrpl/plugin-woocommerce/dev

sudo docker compose --profile tools run --rm wp-cli wp eval '
$order = wc_get_order(<order-id>);

echo "Order: " . $order->get_id() . PHP_EOL;
echo "Status: " . $order->get_status() . PHP_EOL;

foreach ($order->get_meta_data() as $meta) {
    if (str_contains($meta->key, "euroledger")) {
        echo $meta->key . ": " . print_r($meta->value, true) . PHP_EOL;
    }
}
'
```

Expected result:

```text
Status: processing
_euroledger_payment_intent_status: confirmed
_euroledger_webhook_last_event: payment_intent.confirmed
_euroledger_webhook_last_delivery_id: <delivery-id>
```


## Terminal Webhook Events

The WooCommerce receiver also handles terminal non-confirmed events:

```text
payment_intent.expired
payment_intent.cancelled
```

For these events the receiver refreshes EuroLedger metadata and moves an
`on-hold` WooCommerce order to `cancelled`. If the order is no longer on hold,
for example because it is already `processing`, the receiver stores the latest
EuroLedger metadata and adds a note instead of changing the order status.

Expected metadata after an expired or cancelled webhook:

```text
_euroledger_payment_intent_status: expired|cancelled
_euroledger_webhook_last_event: payment_intent.expired|payment_intent.cancelled
_euroledger_webhook_last_delivery_id: <delivery-id>
```

Cancelled events may also include:

```text
_euroledger_payment_intent_cancelled_at: <timestamp>
_euroledger_payment_intent_cancellation_reason: <reason>
```

## Troubleshooting

If `docker compose exec backend ...` reports `service "backend" is not running`,
the command is being executed from the WordPress compose directory. Run backend
commands from the repository root.

If the receiver smoke test returns `200` with HTML, the request is not reaching
the REST receiver. Use the `rest_route` URL shown above and avoid canonical
redirects in local webhook tests.

If confirming a payment intent returns `Cannot confirm payment intent from status
'expired'`, create a new checkout order and confirm the new intent before its
expiry time.

If `webhook-deliveries` is empty after confirmation, check that a webhook
endpoint existed for the merchant before the intent was confirmed. Deliveries are
not generated retroactively for already-confirmed intents.
