#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PLUGIN_SLUG="${PLUGIN_SLUG:-euroledger-xrpl-gateway}"
PLUGIN_SRC="${PLUGIN_SRC:-${REPO_ROOT}/plugin-woocommerce/${PLUGIN_SLUG}}"
DIST_DIR="${DIST_DIR:-${REPO_ROOT}/dist}"
PACKAGE_NAME="${PACKAGE_NAME:-${PLUGIN_SLUG}.zip}"
PACKAGE_PATH="${DIST_DIR}/${PACKAGE_NAME}"
RUN_PHP_LINT="${RUN_PHP_LINT:-auto}"

if [[ ! -d "${PLUGIN_SRC}" ]]; then
  echo "Plugin source directory not found: ${PLUGIN_SRC}" >&2
  exit 1
fi

if [[ ! -f "${PLUGIN_SRC}/${PLUGIN_SLUG}.php" ]]; then
  echo "Plugin bootstrap file not found: ${PLUGIN_SRC}/${PLUGIN_SLUG}.php" >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "zip command is required to build the package." >&2
  exit 1
fi

mkdir -p "${DIST_DIR}"
rm -f "${PACKAGE_PATH}"

BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "${BUILD_DIR}"' EXIT

cp -a "${PLUGIN_SRC}" "${BUILD_DIR}/${PLUGIN_SLUG}"

find "${BUILD_DIR}/${PLUGIN_SLUG}" \
  \( -name '.DS_Store' -o -name 'Thumbs.db' -o -name '__MACOSX' \) \
  -prune -exec rm -rf {} +

find "${BUILD_DIR}/${PLUGIN_SLUG}" \
  \( -name '.git' -o -name '.github' -o -name '.gitea' -o -name 'node_modules' -o -name 'vendor' -o -name '.pytest_cache' -o -name '__pycache__' \) \
  -prune -exec rm -rf {} +

should_lint=0
case "${RUN_PHP_LINT}" in
  1|true|yes) should_lint=1 ;;
  0|false|no) should_lint=0 ;;
  auto)
    if command -v php >/dev/null 2>&1; then
      should_lint=1
    fi
    ;;
  *)
    echo "Invalid RUN_PHP_LINT value: ${RUN_PHP_LINT}. Use auto, true or false." >&2
    exit 1
    ;;
esac

if [[ "${should_lint}" == "1" ]]; then
  while IFS= read -r -d '' php_file; do
    php -l "${php_file}" >/dev/null
  done < <(find "${BUILD_DIR}/${PLUGIN_SLUG}" -type f -name '*.php' -print0)
else
  echo "Skipping PHP lint. Set RUN_PHP_LINT=true to require php -l." >&2
fi

(
  cd "${BUILD_DIR}"
  zip -qr "${PACKAGE_PATH}" "${PLUGIN_SLUG}" \
    -x "*/.DS_Store" \
    -x "*/Thumbs.db" \
    -x "*/__MACOSX/*" \
    -x "*/.git/*" \
    -x "*/.github/*" \
    -x "*/.gitea/*" \
    -x "*/node_modules/*" \
    -x "*/vendor/*" \
    -x "*/__pycache__/*" \
    -x "*/.pytest_cache/*"
)

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "${PACKAGE_PATH}" > "${PACKAGE_PATH}.sha256"
  echo "Checksum: ${PACKAGE_PATH}.sha256"
elif command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "${PACKAGE_PATH}" > "${PACKAGE_PATH}.sha256"
  echo "Checksum: ${PACKAGE_PATH}.sha256"
fi

echo "WooCommerce plugin package created: ${PACKAGE_PATH}"
unzip -l "${PACKAGE_PATH}" | sed -n '1,30p'
