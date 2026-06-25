# Documentation Index

This index is the main entry point for EuroLedger XRPL documentation.

## Project overview

- [Vision](vision.md) — long-term project direction and motivation.
- [Scope](scope.md) — what the project includes and what it explicitly does not include.
- [Architecture](architecture.md) — current high-level architecture notes.
- [Legal disclaimer](legal-disclaimer.md) — legal and financial-service disclaimer.
- [Publication readiness plan](publication-readiness-plan.md) — tasks before making the repository public.

## Backend and payment intents

- [Backend README](../backend/README.md) — local backend development, API docs, workers and tests.
- [Payment intent expiration](payment-intent-expiration.md) — expiration behavior and worker flow.
- [Payment intent dashboard](payment-intent-dashboard.md) — token-protected operational dashboard.

## Merchant webhooks

- [Merchant webhooks](merchant-webhooks.md) — webhook endpoint model and event delivery.
- [Merchant webhook operations](merchant-webhook-operations.md) — operational procedures for webhook delivery.
- [Webhook notifications](webhook-notifications.md) — webhook event notification behavior.
- [Webhook receiver examples](webhook-receiver-examples.md) — example receiver documentation.
- [Standalone webhook receiver example](../examples/webhook_receiver_stdlib.py) — Python stdlib receiver example.

## WooCommerce gateway

- [WooCommerce integration README](../plugin-woocommerce/README.md) — overview of the WooCommerce integration directory.
- [Gateway plugin README](../plugin-woocommerce/euroledger-xrpl-gateway/README.md) — plugin features, configuration and validation.
- [WooCommerce development environment](../plugin-woocommerce/dev/README.md) — local WordPress/WooCommerce dev stack.
- [Merchant installation guide](woocommerce-merchant-installation-guide.md) — merchant-facing installation and configuration guide.
- [Checkout Blocks](woocommerce-checkout-blocks.md) — Checkout Blocks support and validation notes.
- [Webhook development flow](woocommerce-webhook-dev-flow.md) — WooCommerce webhook receiver development flow.
- [Smoke tests](woocommerce-smoke-tests.md) — local WooCommerce smoke and e2e tests.
- [Configuration hardening](woocommerce-plugin-configuration-hardening.md) — gateway configuration validation and admin health checks.
- [Packaging](woocommerce-plugin-packaging.md) — plugin ZIP packaging workflow.
- [Versioning](woocommerce-plugin-versioning.md) — plugin versioning workflow.
- [Release checklist](woocommerce-plugin-release-checklist.md) — release preparation checklist.
- [Gateway 0.1.3 release notes](woocommerce-gateway-0.1.3.md) — developer-facing release notes for `0.1.3`.

## Observability, alerts and automation

- [Observability](observability.md) — Prometheus, Grafana and metrics overview.
- [Alerting](alerting.md) — alerting setup and behavior.
- [Alertmanager routing](alertmanager-routing.md) — Alertmanager routing configuration.
- [n8n Alertmanager workflow](n8n-alertmanager-workflow.md) — n8n workflow for Alertmanager events.
- [n8n Telegram notifications](n8n-telegram-notifications.md) — Telegram notification workflow.
- [Alertmanager n8n workflow exports](../automation/n8n/) — workflow JSON exports.

## CI and quality

- [CI](ci.md) — continuous integration notes.
- [Backend test suite](../backend/tests/) — backend pytest tests.
- [Development scripts](../scripts/dev/README.md) — local scripts for packaging, versioning and WooCommerce smoke tests.

## Releases

- [WooCommerce gateway 0.1.1](releases/woocommerce-gateway-0.1.1.md)
- [WooCommerce gateway 0.1.2](releases/woocommerce-gateway-0.1.2.md)
- [WooCommerce gateway 0.1.3 public release notes](releases/woocommerce-gateway-0.1.3-public.md)

## Internal planning

- [Internal roadmap](internal/roadmap.md) — internal planning notes. Review before public release.

## Suggested reading paths

For backend development, start with [Backend README](../backend/README.md), then read [Architecture](architecture.md), [Merchant webhooks](merchant-webhooks.md), and [Observability](observability.md).

For WooCommerce gateway work, start with [WooCommerce integration README](../plugin-woocommerce/README.md), then read [Gateway plugin README](../plugin-woocommerce/euroledger-xrpl-gateway/README.md), [Checkout Blocks](woocommerce-checkout-blocks.md), and [Smoke tests](woocommerce-smoke-tests.md).

For merchant installation, start with [Merchant installation guide](woocommerce-merchant-installation-guide.md).

For public release preparation, start with [Publication readiness plan](publication-readiness-plan.md).
