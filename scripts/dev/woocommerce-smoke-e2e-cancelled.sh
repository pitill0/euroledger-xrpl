#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREATE_SCRIPT="${ROOT_DIR}/scripts/dev/woocommerce-create-test-order.sh"
CANCELLED_SCRIPT="${ROOT_DIR}/scripts/dev/woocommerce-smoke-cancelled.sh"

if [[ -z "${MERCHANT_API_KEY:-}" ]]; then
  echo "MERCHANT_API_KEY is required" >&2
  exit 1
fi

if [[ ! -x "${CREATE_SCRIPT}" ]]; then
  echo "Missing executable helper: ${CREATE_SCRIPT}" >&2
  exit 1
fi

if [[ ! -x "${CANCELLED_SCRIPT}" ]]; then
  echo "Missing executable smoke test: ${CANCELLED_SCRIPT}" >&2
  exit 1
fi

echo "Creating fresh EuroLedger WooCommerce order for cancelled E2E smoke test..." >&2
create_output="$(${CREATE_SCRIPT})"
echo "${create_output}"

ORDER_ID="$(printf '%s\n' "${create_output}" | sed -n 's/^ORDER_ID=//p' | tail -n 1)"
PAYMENT_INTENT_ID="$(printf '%s\n' "${create_output}" | sed -n 's/^PAYMENT_INTENT_ID=//p' | tail -n 1)"

if [[ -z "${ORDER_ID}" || -z "${PAYMENT_INTENT_ID}" ]]; then
  echo "Unable to extract ORDER_ID/PAYMENT_INTENT_ID from order helper output" >&2
  exit 1
fi

export ORDER_ID PAYMENT_INTENT_ID

echo "Running cancelled smoke test for order ${ORDER_ID} / intent ${PAYMENT_INTENT_ID}..." >&2
"${CANCELLED_SCRIPT}"

echo "Cancelled E2E WooCommerce smoke test completed successfully." >&2
