# WooCommerce Plugin Versioning

This document describes the local versioning workflow for the experimental
EuroLedger XRPL WooCommerce gateway.

## Version locations

The plugin version is stored in the plugin entrypoint:

```text
plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
```

The release version must be kept in sync in two places:

```php
 * Version: 0.1.0
```

and:

```php
define( 'EUROLEDGER_XRPL_GATEWAY_VERSION', '0.1.0' );
```

The `EUROLEDGER_XRPL_GATEWAY_VERSION` constant exists so future admin assets,
cache-busting and diagnostics can use the same version as the WordPress plugin
metadata.

If the plugin README later gains a WordPress-style `Stable tag:` field, it must
match the same version.

## Update the version

Use the helper script from the repository root:

```bash
scripts/dev/set-woocommerce-plugin-version.sh 0.1.1
```

The script updates:

```text
- plugin header Version
- EUROLEDGER_XRPL_GATEWAY_VERSION
- plugin README Stable tag, when present
```

It also runs `php -l` on the plugin entrypoint when PHP is available.

## Recommended release flow

Before packaging a plugin build:

```bash
git status --short
scripts/dev/set-woocommerce-plugin-version.sh <version>
php -l plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
scripts/dev/woocommerce-smoke-e2e-confirmed.sh
scripts/dev/woocommerce-smoke-e2e-cancelled.sh
scripts/dev/package-woocommerce-plugin.sh
unzip -l dist/euroledger-xrpl-gateway.zip | head -40
```

Then commit the version bump separately from feature work when possible:

```bash
git add plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
git commit -m "chore: bump WooCommerce plugin version to <version>"
```

## Versioning policy

Use semantic versions while the plugin is experimental:

```text
0.1.0  initial local gateway flow
0.1.1  patch/fix without new behavior
0.2.0  new user-visible or operational behavior
```

Until the plugin is production-ready, keep versions in the `0.x.y` range.
