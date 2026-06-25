# EuroLedger XRPL SDK

This directory is reserved for future SDKs and integration clients for EuroLedger XRPL.

The backend API is already usable directly through HTTP. This directory exists to provide typed, reusable client libraries once the public API stabilizes further.

## Intended scope

Future SDKs may include:

- Python client for backend API usage.
- PHP client helpers for merchant integrations.
- JavaScript/TypeScript client for admin dashboards or external tools.
- Shared webhook signature verification helpers.
- Payment intent helper methods.
- Typed API request and response models.
- Local testing utilities for merchant integrations.

## Current status

```text
planned
```

There is no production SDK in this directory yet.

Current integrations use the backend HTTP API directly. The WooCommerce gateway contains its own PHP API client under:

```text
plugin-woocommerce/euroledger-xrpl-gateway/includes/class-euroledger-xrpl-api-client.php
```

## Recommended first milestone

A first SDK milestone should focus on the smallest useful surface:

```text
create payment intent
get payment intent
list payment intents
confirm payment intent for test/dev flows
cancel payment intent
verify webhook signature
parse webhook event payloads
```

## Design principles

SDKs should be:

- thin wrappers over the documented HTTP API;
- explicit about merchant API key authentication;
- easy to test without XRPL access;
- safe by default with clear timeout and error handling;
- versioned independently when needed.

## Related documentation

- `docs/backend-api-and-operations.md`
- `docs/merchant-webhooks.md`
- `docs/webhook-receiver-examples.md`
- `examples/webhook_receiver_stdlib.py`
