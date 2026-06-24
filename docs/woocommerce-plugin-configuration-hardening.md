# WooCommerce Gateway Configuration Hardening

This guide summarizes the EuroLedger XRPL WooCommerce gateway configuration checks.

## Checkout readiness

The gateway is only offered at checkout when all blocking settings are present:

- gateway is enabled;
- API base URL is configured and uses `http` or `https`;
- merchant API key is configured;
- webhook secret is configured.

The webhook secret is treated as required because orders rely on signed webhook
callbacks to move from `on-hold` to `processing`, `cancelled` or `expired`
terminal handling. Without it, checkout could create orders that never update
safely.

## Configuration health panel

The gateway settings screen includes a **Configuration health** panel with:

- blocking errors;
- warnings that should be reviewed before release;
- informational notices;
- success checks for required settings.

The panel is shown in:

```text
WooCommerce > Settings > Payments > EuroLedger XRPL
```

If the gateway is enabled but a blocking setting is missing, the same settings
screen also shows an admin error notice explaining why the gateway is not ready.

## Dashboard URL checks

The dashboard URL is optional. When it is empty, admin dashboard links are hidden.

When configured, the plugin checks for common mistakes:

- invalid URL scheme;
- raw backend API root, such as `http://localhost:8000`, which opens API routes
  in the browser and usually returns `Missing API key`;
- direct `/payment-intents/...` API URLs instead of the HTML dashboard route;
- `/dashboard` without `?token=...` for the current development dashboard;
- plain HTTP on non-local hosts.

For local development, use:

```text
http://localhost:8000/dashboard?token=<dashboard-token>
```

The plugin preserves query parameters and builds links like:

```text
http://localhost:8000/dashboard/payment-intents/<payment-intent-id>?token=<dashboard-token>
```

## Backend connection check

The existing **Check backend connection** button remains available. It verifies:

- backend health via `/health`;
- merchant authentication via `/auth/me`.

Run this check after reviewing the configuration health panel.
