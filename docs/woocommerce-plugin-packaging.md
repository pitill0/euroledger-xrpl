# WooCommerce plugin packaging

This guide explains how to build an installable ZIP for the EuroLedger XRPL
WooCommerce gateway.

The packaging script creates:

```text
dist/euroledger-xrpl-gateway.zip
```

The ZIP root contains the WordPress plugin folder:

```text
euroledger-xrpl-gateway/
```

This is the structure WordPress expects when uploading a plugin ZIP from the
admin plugins screen.

## Build

From the repository root:

```bash
scripts/dev/package-woocommerce-plugin.sh
```

The script packages:

```text
plugin-woocommerce/euroledger-xrpl-gateway/
```

and writes the artifact to:

```text
dist/euroledger-xrpl-gateway.zip
```

It also writes a SHA-256 checksum when `sha256sum` or `shasum` is available:

```text
dist/euroledger-xrpl-gateway.zip.sha256
```

## Validation

When PHP is available, the script runs `php -l` over all plugin PHP files before
creating the ZIP. To force linting or skip it explicitly:

```bash
RUN_PHP_LINT=true scripts/dev/package-woocommerce-plugin.sh
RUN_PHP_LINT=false scripts/dev/package-woocommerce-plugin.sh
```

## Custom output

The package name and output directory can be overridden:

```bash
DIST_DIR=/tmp/euroledger-builds \
PACKAGE_NAME=euroledger-xrpl-gateway-dev.zip \
scripts/dev/package-woocommerce-plugin.sh
```

## Install test

A quick manual install test is:

1. Build the ZIP.
2. Open WordPress admin.
3. Go to `Plugins > Add New Plugin > Upload Plugin`.
4. Upload `dist/euroledger-xrpl-gateway.zip`.
5. Activate **EuroLedger XRPL Gateway**.
6. Open `WooCommerce > Settings > Payments > EuroLedger XRPL`.

For local development, the plugin is usually mounted directly into the WordPress
container. The packaging script is intended for install testing and release
artifacts, not for the normal mounted dev loop.

## Release checklist

Before sharing a package, run the local checks that apply to the change:

```bash
php -l plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-gateway.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-webhook-receiver.php
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-admin-order-meta.php

git diff --check -- plugin-woocommerce scripts/dev docs/woocommerce-plugin-packaging.md
```

Recommended smoke checks before release:

```bash
export MERCHANT_API_KEY='...'

scripts/dev/woocommerce-smoke-e2e-confirmed.sh
scripts/dev/woocommerce-smoke-e2e-cancelled.sh
```

Then build the release ZIP:

```bash
scripts/dev/package-woocommerce-plugin.sh
```
