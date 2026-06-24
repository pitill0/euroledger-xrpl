# EuroLedger XRPL WooCommerce Gateway v0.1.2

## Summary

EuroLedger XRPL WooCommerce Gateway v0.1.2 is a configuration hardening release.

This version improves the safety and usability of the WooCommerce gateway settings by adding configuration health checks, checkout readiness validation, and clearer warnings for common setup mistakes.

## Changes

### Added

- Configuration health panel in the EuroLedger XRPL payment gateway settings.
- Checkout readiness validation.
- Admin warnings when the gateway is enabled but not ready for checkout.
- Dashboard URL validation warnings.
- Documentation for configuration hardening.
- Release checklist updates.

### Improved

- The gateway is only available at checkout when the required configuration is present:
  - EuroLedger API base URL
  - Merchant API key
  - Webhook secret

- Dashboard configuration now warns about common mistakes:
  - raw backend API root URLs,
  - `/payment-intents` API URLs,
  - `/dashboard` URLs without token,
  - invalid URLs,
  - plain HTTP outside local/dev hosts.

### Internal

- Backend tests were adjusted to isolate dashboard token environment variables.
- Alembic migrations were cleaned up for Ruff compatibility.

## Upgrade notes

After upgrading, review:

```text
WooCommerce > Settings > Payments > EuroLedger XRPL
```

The new **Configuration health** section should show whether the gateway is ready for checkout.

If the gateway is enabled but required settings are missing, the payment method will not appear during checkout.

## Validation

Recommended validation before packaging:

```bash
php -l plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-gateway.php

sudo docker compose exec backend pytest

scripts/dev/woocommerce-smoke-e2e-confirmed.sh
scripts/dev/woocommerce-smoke-e2e-cancelled.sh

scripts/dev/package-woocommerce-plugin.sh
```

## Known limitations

- WooCommerce Checkout Blocks are still not supported.
- Dashboard token authentication remains a development/internal mechanism.
- Production hardening is still pending before real merchant deployment.
