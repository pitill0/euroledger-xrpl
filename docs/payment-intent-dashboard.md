# Payment Intent Dashboard

EuroLedger exposes a small HTML dashboard view for development and operational
inspection of a single payment intent:

```text
GET /dashboard/payment-intents/{payment_intent_id}?token={dashboard-token}
```

The dashboard is intended for browser links from integrations such as the
WooCommerce admin order screen. It does not use `X-API-Key` because normal HTML
links cannot send API headers.

## Configuration

Set `DASHBOARD_TOKEN` in the backend environment:

```env
DASHBOARD_TOKEN=replace-with-a-random-development-token
```

When the token is empty or unset, dashboard views are disabled and return 404.
When the token is missing or invalid, the route returns 401.

## WooCommerce dev configuration

Configure the WooCommerce gateway **Dashboard base URL** with the token included
as a query parameter:

```text
http://localhost:8000/dashboard?token=replace-with-a-random-development-token
```

The gateway preserves query parameters when building payment intent links, so an
order link becomes:

```text
http://localhost:8000/dashboard/payment-intents/{payment_intent_id}?token=replace-with-a-random-development-token
```

## Contents

The dashboard page shows:

- payment intent reference, id, merchant id, amount, status and timestamps;
- XRPL transaction hash and expected destination when present;
- cancellation details when present;
- recent webhook deliveries for the payment intent.

This is a development dashboard, not a full merchant portal. Use a strong token,
keep it out of public logs and do not expose this route publicly without a real
authentication layer.
