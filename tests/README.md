# EuroLedger XRPL Top-Level Tests

This directory is reserved for repository-level tests that span multiple project components.

Backend unit and API tests currently live in:

```text
backend/tests/
```

WooCommerce smoke and end-to-end validation scripts currently live in:

```text
scripts/dev/
```

## Intended scope

Future top-level tests may include:

- full Docker Compose integration tests;
- backend plus PostgreSQL migration validation;
- XRPL worker plus fixture-based reconciliation flows;
- merchant webhook delivery end-to-end tests;
- WooCommerce gateway integration tests;
- release package validation;
- public documentation link checks.

## Current status

```text
planned
```

There are no top-level cross-component tests yet.

## Suggested first milestones

### 1. Compose health test

Validate that the local stack starts and exposes:

```text
GET /health
GET /health/ready
GET /metrics
```

### 2. Migration test

Start a clean database and run:

```text
alembic upgrade head
```

Then verify that the backend readiness endpoint reports a healthy migration state.

### 3. Webhook delivery integration test

Create a merchant, configure a webhook endpoint, confirm a payment intent, and verify that a delivery is queued and delivered to a local receiver.

### 4. WooCommerce package smoke test

Install the packaged plugin ZIP into the local WooCommerce dev environment and run the confirmed/cancelled smoke flows.

## Related documentation

- `backend/tests/`
- `docs/backend-api-and-operations.md`
- `docs/woocommerce-smoke-tests.md`
- `docs/merchant-webhook-operations.md`
- `scripts/dev/`
