# Local WooCommerce Dev Environment

This environment is only for local EuroLedger XRPL gateway development. It must
not be connected to a production WordPress installation.

The compose file intentionally uses recent WordPress and WP-CLI images by
default so that the latest WooCommerce plugin can be installed from wp.org.
Override the images through environment variables if a compatibility test needs
an older WordPress version.

## Start

```bash
cd plugin-woocommerce/dev
sudo docker compose up -d
```

Open:

```text
http://localhost:8088
```

## Validate the Database

MariaDB may need a few seconds before WordPress can connect. Check it explicitly:

```bash
sudo docker compose --profile tools run --rm wp-cli wp db check
```

Expected output:

```text
Success: Database checked.
```

## Install WordPress

```bash
sudo docker compose --profile tools run --rm wp-cli wp core install \
  --url="http://localhost:8088" \
  --title="EuroLedger WooCommerce Dev" \
  --admin_user="admin" \
  --admin_password="admin" \
  --admin_email="admin@example.test" \
  --skip-email
```

## Install WooCommerce

```bash
sudo docker compose --profile tools run --rm wp-cli wp plugin install \
  woocommerce \
  --activate
```

If this reports that WooCommerce requires a newer WordPress version, refresh the
containers with the default latest images:

```bash
sudo docker compose down -v
sudo docker compose pull
sudo docker compose up -d
```

## Activate EuroLedger XRPL Gateway

```bash
sudo docker compose --profile tools run --rm wp-cli wp plugin activate \
  euroledger-xrpl-gateway
```

Then open:

```text
http://localhost:8088/wp-admin/admin.php?page=wc-settings&tab=checkout&section=euroledger_xrpl
```

## Connect to the Backend

When WordPress runs inside a container, `localhost` points to the WordPress
container itself. Use one of these API base URLs for a backend running on the
host:

```text
http://host.containers.internal:8000
http://host.docker.internal:8000
```

## Stop and Reset

Stop without deleting data:

```bash
sudo docker compose down
```

Reset all WordPress and database data:

```bash
sudo docker compose down -v
```
