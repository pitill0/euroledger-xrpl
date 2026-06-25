# EuroLedger XRPL Documentation Index

This index maps the main documentation areas for EuroLedger XRPL.

## Start here

- [Project overview](../README.md)
- [Architecture](architecture.md)
- [Scope](scope.md)
- [Vision](vision.md)
- [Legal disclaimer](legal-disclaimer.md)
- [Publication readiness plan](publication-readiness-plan.md)

## Backend and API

- [Backend README](../backend/README.md)
- [Payment intent expiration](payment-intent-expiration.md)
- [Payment intent dashboard](payment-intent-dashboard.md)
- [CI](ci.md)

## XRPL payment processing

The XRPL worker scans account transactions, extracts payment references from memos, validates candidate payments, and confirms matching payment intents.

Relevant documentation:

- [Architecture](architecture.md)
- [Payment intent expiration](payment-intent-expiration.md)

## Merchant webhooks

Merchant webhooks notify external systems when EuroLedger payment intents change state.

Core documentation:

- [Merchant webhooks](merchant-webhooks.md)
- [Merchant webhook operations](merchant-webhook-operations.md)
- [Webhook notifications](webhook-notifications.md)
- [Webhook receiver examples](webhook-receiver-examples.md)

## WooCommerce gateway

The WooCommerce gateway connects WooCommerce orders with EuroLedger XRPL payment intents.

### Merchant-facing documentation

Read these when installing or configuring the plugin in a store:

- [WooCommerce merchant installation guide](woocommerce-merchant-installation-guide.md)
- [WooCommerce gateway 0.1.3 release notes](woocommerce-gateway-0.1.3.md)
- [WooCommerce gateway 0.1.3 public release notes](releases/woocommerce-gateway-0.1.3-public.md)

### Plugin developer documentation

Read these when developing, testing, or maintaining the WooCommerce plugin:

- [WooCommerce integration README](../plugin-woocommerce/README.md)
- [Gateway plugin README](../plugin-woocommerce/euroledger-xrpl-gateway/README.md)
- [WooCommerce webhook development flow](woocommerce-webhook-dev-flow.md)
- [WooCommerce Checkout Blocks](woocommerce-checkout-blocks.md)
- [WooCommerce smoke tests](woocommerce-smoke-tests.md)

### Release and operations documentation

Read these when preparing a plugin release or validating configuration:

- [WooCommerce plugin packaging](woocommerce-plugin-packaging.md)
- [WooCommerce plugin release checklist](woocommerce-plugin-release-checklist.md)
- [WooCommerce plugin versioning](woocommerce-plugin-versioning.md)
- [WooCommerce plugin configuration hardening](woocommerce-plugin-configuration-hardening.md)

## Observability and alerting

EuroLedger includes Prometheus metrics, Grafana dashboards, Alertmanager routing, and n8n Telegram notification workflows.

- [Observability](observability.md)
- [Alerting](alerting.md)
- [Alertmanager routing](alertmanager-routing.md)
- [n8n Alertmanager workflow](n8n-alertmanager-workflow.md)
- [n8n Telegram notifications](n8n-telegram-notifications.md)

## Releases

WooCommerce gateway release documentation:

- [WooCommerce gateway 0.1.1](releases/woocommerce-gateway-0.1.1.md)
- [WooCommerce gateway 0.1.2](releases/woocommerce-gateway-0.1.2.md)
- [WooCommerce gateway 0.1.3 public release](releases/woocommerce-gateway-0.1.3-public.md)

Current WooCommerce gateway version:

```text
0.1.3
```

## Internal documents

- [Internal roadmap](internal/roadmap.md)

Internal documents are useful while developing the project, but should be reviewed before making the repository public.
