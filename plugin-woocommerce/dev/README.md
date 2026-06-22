# Local WooCommerce Development Environment

This directory provides an isolated WordPress/WooCommerce environment for testing the EuroLedger XRPL gateway plugin without touching production.

## Start WordPress

```bash
cd plugin-woocommerce/dev
docker compose up -d
```

Open:

```text
http://localhost:8088
```

The plugin source is mounted from the repository into WordPress:

```text
/wp-content/plugins/euroledger-xrpl-gateway
```

Changes made in `plugin-woocommerce/euroledger-xrpl-gateway/` are visible inside the WordPress container after a page refresh.

## Install WordPress and WooCommerce with WP-CLI

After the containers are up, install WordPress:

```bash
docker compose --profile tools run --rm wp-cli wp core install \
  --url="http://localhost:8088" \
  --title="EuroLedger WooCommerce Dev" \
  --admin_user="admin" \
  --admin_password="admin" \
  --admin_email="admin@example.test" \
  --skip-email
```

Install and activate WooCommerce:

```bash
docker compose --profile tools run --rm wp-cli wp plugin install woocommerce --activate
```

Activate the EuroLedger XRPL gateway:

```bash
docker compose --profile tools run --rm wp-cli wp plugin activate euroledger-xrpl-gateway
```

Then open:

```text
http://localhost:8088/wp-admin/admin.php?page=wc-settings&tab=checkout&section=euroledger_xrpl
```

Login credentials for the local environment:

```text
Username: admin
Password: admin
```

These credentials are only for the local disposable environment.

## Connect to the local EuroLedger backend

If the EuroLedger backend is running from the repository root with Docker Compose, the WordPress container must reach it through the container host, not `localhost`.

Use one of these API base URLs in the gateway settings, depending on your container runtime:

```text
http://host.containers.internal:8000
http://host.docker.internal:8000
```

Do not use `http://localhost:8000` from inside WordPress unless the backend is running in the same container.

## Reset the environment

To remove local WordPress and database data:

```bash
cd plugin-woocommerce/dev
docker compose down -v
```
