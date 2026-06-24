#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WP_DEV_DIR="${WP_DEV_DIR:-${ROOT_DIR}/plugin-woocommerce/dev}"
DOCKER_COMPOSE="${DOCKER_COMPOSE:-sudo docker compose}"
SMOKE_PRODUCT_SKU="${SMOKE_PRODUCT_SKU:-euroledger-smoke-test-product}"
SMOKE_PRODUCT_NAME="${SMOKE_PRODUCT_NAME:-EuroLedger Smoke Test Product}"
SMOKE_PRODUCT_PRICE="${SMOKE_PRODUCT_PRICE:-5.00}"
SMOKE_CURRENCY="${SMOKE_CURRENCY:-EUR}"
SMOKE_CUSTOMER_EMAIL="${SMOKE_CUSTOMER_EMAIL:-smoke-test@example.test}"

wp_eval() {
  local code="$1"
  (cd "${WP_DEV_DIR}" && ${DOCKER_COMPOSE} --profile tools run --rm \
    -e SMOKE_PRODUCT_SKU="${SMOKE_PRODUCT_SKU}" \
    -e SMOKE_PRODUCT_NAME="${SMOKE_PRODUCT_NAME}" \
    -e SMOKE_PRODUCT_PRICE="${SMOKE_PRODUCT_PRICE}" \
    -e SMOKE_CURRENCY="${SMOKE_CURRENCY}" \
    -e SMOKE_CUSTOMER_EMAIL="${SMOKE_CUSTOMER_EMAIL}" \
    wp-cli wp eval "${code}")
}

echo "Creating EuroLedger WooCommerce smoke test order..." >&2

wp_eval '
if (!class_exists("WooCommerce")) {
    echo "WooCommerce is not loaded" . PHP_EOL;
    exit(1);
}

$gateways = WC()->payment_gateways()->payment_gateways();
if (!isset($gateways["euroledger_xrpl"])) {
    echo "EuroLedger XRPL gateway is not registered" . PHP_EOL;
    exit(1);
}

$gateway = $gateways["euroledger_xrpl"];
if ("yes" !== $gateway->enabled) {
    echo "EuroLedger XRPL gateway is disabled" . PHP_EOL;
    exit(1);
}

$sku = getenv("SMOKE_PRODUCT_SKU") ?: "euroledger-smoke-test-product";
$name = getenv("SMOKE_PRODUCT_NAME") ?: "EuroLedger Smoke Test Product";
$price = getenv("SMOKE_PRODUCT_PRICE") ?: "5.00";
$currency = getenv("SMOKE_CURRENCY") ?: "EUR";
$email = getenv("SMOKE_CUSTOMER_EMAIL") ?: "smoke-test@example.test";

$product_id = wc_get_product_id_by_sku($sku);
$product = $product_id ? wc_get_product($product_id) : null;

if (!$product instanceof WC_Product) {
    $product = new WC_Product_Simple();
    $product->set_name($name);
    $product->set_sku($sku);
    $product->set_regular_price($price);
    $product->set_price($price);
    $product->set_status("publish");
    $product->set_catalog_visibility("hidden");
    $product_id = $product->save();
} else {
    $product->set_regular_price($price);
    $product->set_price($price);
    $product->save();
    $product_id = $product->get_id();
}

if (!$product_id) {
    echo "Unable to create or load smoke test product" . PHP_EOL;
    exit(1);
}

$order = wc_create_order();
if (is_wp_error($order)) {
    echo "Unable to create WooCommerce order: " . $order->get_error_message() . PHP_EOL;
    exit(1);
}

$order->add_product(wc_get_product($product_id), 1);
$order->set_currency($currency);
$order->set_billing_first_name("EuroLedger");
$order->set_billing_last_name("Smoke Test");
$order->set_billing_email($email);
$order->set_payment_method("euroledger_xrpl");
$order->set_payment_method_title($gateway->get_title());
$order->calculate_totals();
$order->save();

// The gateway empties WC()->cart after creating the payment intent. In WP-CLI
// there is no browser session, so initialise the minimal WooCommerce runtime
// pieces required by process_payment().
if (null === WC()->session) {
    WC()->session = new WC_Session_Handler();
    WC()->session->init();
}
if (null === WC()->customer) {
    WC()->customer = new WC_Customer(0, true);
}
if (null === WC()->cart) {
    WC()->cart = new WC_Cart();
}

$result = $gateway->process_payment($order->get_id());
$order = wc_get_order($order->get_id());

if (!is_array($result) || "success" !== ($result["result"] ?? "")) {
    echo "EuroLedger gateway process_payment failed" . PHP_EOL;

    $notices = wc_get_notices("error");
    foreach ($notices as $notice) {
        $message = is_array($notice) ? ($notice["notice"] ?? "") : (string) $notice;
        if ("" !== $message) {
            echo "NOTICE=" . wp_strip_all_tags($message) . PHP_EOL;
        }
    }

    echo "ORDER_ID=" . $order->get_id() . PHP_EOL;
    echo "ORDER_STATUS=" . $order->get_status() . PHP_EOL;
    exit(1);
}

echo "ORDER_ID=" . $order->get_id() . PHP_EOL;
echo "ORDER_STATUS=" . $order->get_status() . PHP_EOL;
echo "PAYMENT_INTENT_ID=" . $order->get_meta("_euroledger_payment_intent_id") . PHP_EOL;
echo "REFERENCE=" . $order->get_meta("_euroledger_payment_intent_reference") . PHP_EOL;
echo "EUROLEDGER_STATUS=" . $order->get_meta("_euroledger_payment_intent_status") . PHP_EOL;
echo "ORDER_RECEIVED_URL=" . $order->get_checkout_order_received_url() . PHP_EOL;
'
