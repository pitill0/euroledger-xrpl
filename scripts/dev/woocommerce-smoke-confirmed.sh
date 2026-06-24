#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WP_DEV_DIR="${WP_DEV_DIR:-${ROOT_DIR}/plugin-woocommerce/dev}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
DOCKER_COMPOSE="${DOCKER_COMPOSE:-sudo docker compose}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-60}"

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

api_get() {
  curl -fsS "$1" -H "X-API-Key: ${MERCHANT_API_KEY}"
}

api_post_json() {
  curl -fsS -X POST "$1" \
    -H "X-API-Key: ${MERCHANT_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$2"
}

wp_eval() {
  local code="$1"
  (cd "${WP_DEV_DIR}" && ${DOCKER_COMPOSE} --profile tools run --rm wp-cli wp eval "${code}")
}

wp_eval_with_order() {
  local code="$1"
  (cd "${WP_DEV_DIR}" && ${DOCKER_COMPOSE} --profile tools run --rm -e ORDER_ID="${ORDER_ID}" wp-cli wp eval "${code}")
}

extract_assignment() {
  local name="$1"
  awk -F= -v key="${name}" '$1 == key {print substr($0, length(key) + 2); exit}'
}

latest_pending_order_candidates() {
  wp_eval '''
$orders = wc_get_orders([
    "limit" => 50,
    "orderby" => "date",
    "order" => "DESC",
    "payment_method" => "euroledger_xrpl",
]);

foreach ($orders as $order) {
    if ("on-hold" !== $order->get_status()) {
        continue;
    }

    if ("pending" !== $order->get_meta("_euroledger_payment_intent_status")) {
        continue;
    }

    echo "ORDER_ID=" . $order->get_id() . PHP_EOL;
    echo "PAYMENT_INTENT_ID=" . $order->get_meta("_euroledger_payment_intent_id") . PHP_EOL;
    echo "REFERENCE=" . $order->get_meta("_euroledger_payment_intent_reference") . PHP_EOL;
    echo "---" . PHP_EOL;
}
'''
}

select_pending_order() {
  local candidates block candidate_order candidate_intent candidate_reference status response

  candidates="$(latest_pending_order_candidates)"

  while IFS= read -r block; do
    if [[ -z "${block}" ]]; then
      continue
    fi

    candidate_order="$(printf '%s
' "${block}" | extract_assignment ORDER_ID)"
    candidate_intent="$(printf '%s
' "${block}" | extract_assignment PAYMENT_INTENT_ID)"
    candidate_reference="$(printf '%s
' "${block}" | extract_assignment REFERENCE)"

    if [[ -z "${candidate_order}" || -z "${candidate_intent}" ]]; then
      continue
    fi

    response="$(api_get "${BACKEND_URL}/payment-intents/${candidate_intent}" 2>/dev/null || true)"
    if [[ -z "${response}" ]]; then
      echo "Skipping order ${candidate_order}: payment intent ${candidate_intent} not found in backend" >&2
      continue
    fi

    status="$(printf '%s
' "${response}" | json_field status)"
    if [[ "${status}" != "pending" ]]; then
      echo "Skipping order ${candidate_order}: backend payment intent status is ${status}" >&2
      continue
    fi

    echo "ORDER_ID=${candidate_order}"
    echo "PAYMENT_INTENT_ID=${candidate_intent}"
    echo "REFERENCE=${candidate_reference}"
    return 0
  done < <(printf '%s
' "${candidates}" | awk '
    BEGIN { block="" }
    /^---$/ { print block; block=""; next }
    { block = block $0 "\n" }
    END { if (block != "") print block }
  ')

  echo "No pending EuroLedger on-hold order found with backend status pending" >&2
  return 1
}

json_field() {
  local field="$1"
  python -c 'import json,sys
field=sys.argv[1]
data=json.load(sys.stdin)
value=data
for part in field.split("."):
    if isinstance(value, dict):
        value=value.get(part)
    else:
        value=None
        break
print("" if value is None else value)
' "${field}"
}

delivery_status() {
  python -c 'import json,sys
items=json.load(sys.stdin).get("items", [])
if not items:
    print("none")
    sys.exit(0)
item=items[0]
print("%s|%s|%s|%s" % (
    item.get("id", ""),
    item.get("status", ""),
    item.get("response_status_code", ""),
    item.get("error_message") or "",
))
'
}

wait_for_delivery() {
  local deadline=$((SECONDS + MAX_WAIT_SECONDS))
  local status_line status

  while (( SECONDS < deadline )); do
    status_line="$(api_get "${BACKEND_URL}/webhook-deliveries?payment_intent_id=${PAYMENT_INTENT_ID}" | delivery_status)"
    IFS='|' read -r DELIVERY_ID status RESPONSE_STATUS ERROR_MESSAGE <<< "${status_line}"

    echo "delivery=${DELIVERY_ID:-none} status=${status:-none} response=${RESPONSE_STATUS:-none}"

    case "${status}" in
      delivered)
        return 0
        ;;
      failed|discarded)
        echo "Webhook delivery ended in ${status}: ${ERROR_MESSAGE}" >&2
        return 1
        ;;
    esac

    sleep 2
  done

  echo "Timed out waiting for webhook delivery to be delivered" >&2
  return 1
}

verify_order() {
  wp_eval_with_order '
$order = wc_get_order((int) getenv("ORDER_ID"));
if (!$order) {
    echo "Order not found" . PHP_EOL;
    exit(1);
}

$status = $order->get_status();
$euroledger_status = $order->get_meta("_euroledger_payment_intent_status");
$event = $order->get_meta("_euroledger_webhook_last_event");
$hash = $order->get_meta("_euroledger_xrpl_transaction_hash");

echo "ORDER_ID=" . $order->get_id() . PHP_EOL;
echo "ORDER_STATUS=" . $status . PHP_EOL;
echo "EUROLEDGER_STATUS=" . $euroledger_status . PHP_EOL;
echo "LAST_EVENT=" . $event . PHP_EOL;
echo "XRPL_HASH=" . $hash . PHP_EOL;

if ("processing" !== $status) {
    echo "Expected WooCommerce order status processing" . PHP_EOL;
    exit(1);
}

if ("confirmed" !== $euroledger_status) {
    echo "Expected EuroLedger status confirmed" . PHP_EOL;
    exit(1);
}

if ("payment_intent.confirmed" !== $event) {
    echo "Expected last event payment_intent.confirmed" . PHP_EOL;
    exit(1);
}

if ("" === $hash) {
    echo "Expected XRPL transaction hash" . PHP_EOL;
    exit(1);
}
'
}

require_env MERCHANT_API_KEY

if [[ -n "${ORDER_ID:-}" || -n "${PAYMENT_INTENT_ID:-}" ]]; then
  if [[ -z "${ORDER_ID:-}" || -z "${PAYMENT_INTENT_ID:-}" ]]; then
    echo "When using explicit values, set both ORDER_ID and PAYMENT_INTENT_ID." >&2
    exit 1
  fi
else
  echo "Discovering latest pending EuroLedger order..."
  discovery="$(select_pending_order)"
  echo "${discovery}"
  ORDER_ID="$(printf '%s\n' "${discovery}" | extract_assignment ORDER_ID)"
  PAYMENT_INTENT_ID="$(printf '%s\n' "${discovery}" | extract_assignment PAYMENT_INTENT_ID)"
fi

if [[ -z "${ORDER_ID}" || -z "${PAYMENT_INTENT_ID}" ]]; then
  echo "Could not determine ORDER_ID/PAYMENT_INTENT_ID" >&2
  exit 1
fi

backend_status="$(api_get "${BACKEND_URL}/payment-intents/${PAYMENT_INTENT_ID}" | json_field status)"
if [[ "${backend_status}" != "pending" ]]; then
  echo "Payment intent ${PAYMENT_INTENT_ID} for order ${ORDER_ID} is ${backend_status}, expected pending." >&2
  echo "Create a new WooCommerce EuroLedger order or unset stale ORDER_ID/PAYMENT_INTENT_ID values." >&2
  exit 1
fi

XRPL_HASH="${XRPL_HASH:-$(python - <<'PY'
print("f" * 64)
PY
)}"

echo "Confirming payment intent ${PAYMENT_INTENT_ID} for order ${ORDER_ID}..."
confirm_response="$(api_post_json "${BACKEND_URL}/payment-intents/${PAYMENT_INTENT_ID}/confirm" "{\"xrpl_transaction_hash\":\"${XRPL_HASH}\"}")"
printf '%s\n' "${confirm_response}" | python -m json.tool

status="$(printf '%s\n' "${confirm_response}" | json_field status)"
if [[ "${status}" != "confirmed" ]]; then
  echo "Expected payment intent status confirmed, got ${status}" >&2
  exit 1
fi

echo "Running webhook worker once. This may process 0 items if the automatic worker was faster..."
(cd "${ROOT_DIR}" && ${DOCKER_COMPOSE} exec -T backend python -m app.commands.webhook_worker --limit 100 --timeout 10 --max-attempts 5) || true

wait_for_delivery
verify_order

echo "Confirmed smoke test passed for order ${ORDER_ID}."
