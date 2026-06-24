#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/dev/set-woocommerce-plugin-version.sh <version>

Examples:
  scripts/dev/set-woocommerce-plugin-version.sh 0.1.1
  scripts/dev/set-woocommerce-plugin-version.sh 0.2.0-beta.1

Updates:
  - plugin header: Version: <version>
  - PHP constant: EUROLEDGER_XRPL_GATEWAY_VERSION
  - plugin readme Stable tag, when present
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

VERSION="${1:-}"

if [[ -z "${VERSION}" ]]; then
  usage >&2
  exit 2
fi

if [[ ! "${VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z]+)*$ ]]; then
  echo "Invalid version: ${VERSION}" >&2
  echo "Expected semantic version like 0.1.1 or 0.2.0-beta.1" >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN_MAIN="${REPO_ROOT}/plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php"
PLUGIN_README="${REPO_ROOT}/plugin-woocommerce/euroledger-xrpl-gateway/README.md"

if [[ ! -f "${PLUGIN_MAIN}" ]]; then
  echo "Plugin main file not found: ${PLUGIN_MAIN}" >&2
  exit 1
fi

python - "${VERSION}" "${PLUGIN_MAIN}" "${PLUGIN_README}" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

version = sys.argv[1]
plugin_main = Path(sys.argv[2])
plugin_readme = Path(sys.argv[3])

main_text = plugin_main.read_text(encoding="utf-8")

updates: list[str] = []

main_text, count = re.subn(
    r"(?m)^( \* Version:\s*).+$",
    rf"\g<1>{version}",
    main_text,
    count=1,
)
if count != 1:
    raise SystemExit("Could not update plugin header Version.")
updates.append("plugin header Version")

main_text, count = re.subn(
    r"define\(\s*'EUROLEDGER_XRPL_GATEWAY_VERSION'\s*,\s*'[^']+'\s*\);",
    f"define( 'EUROLEDGER_XRPL_GATEWAY_VERSION', '{version}' );",
    main_text,
    count=1,
)
if count != 1:
    raise SystemExit("Could not update EUROLEDGER_XRPL_GATEWAY_VERSION constant.")
updates.append("EUROLEDGER_XRPL_GATEWAY_VERSION")

plugin_main.write_text(main_text, encoding="utf-8")

if plugin_readme.exists():
    readme_text = plugin_readme.read_text(encoding="utf-8")
    readme_text, count = re.subn(
        r"(?mi)^(Stable tag:\s*).+$",
        rf"\g<1>{version}",
        readme_text,
        count=1,
    )
    if count:
        plugin_readme.write_text(readme_text, encoding="utf-8")
        updates.append("plugin README Stable tag")

print("Updated WooCommerce plugin version to", version)
for item in updates:
    print("-", item)
PY

if command -v php >/dev/null 2>&1; then
  php -l "${PLUGIN_MAIN}" >/dev/null
  echo "PHP syntax OK: ${PLUGIN_MAIN#"${REPO_ROOT}/"}"
else
  echo "PHP not available; skipped php -l validation."
fi
