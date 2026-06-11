# Observability

EuroLedger XRPL includes an optional local observability stack based on Prometheus and Grafana.

## Components

- FastAPI exposes worker metrics through `/metrics`.
- Prometheus scrapes the backend through the internal Compose network.
- Grafana uses Prometheus as its default datasource.
- The XRPL worker dashboard is provisioned automatically.
- Prometheus and Grafana data are stored in persistent Compose volumes.

## Start the Stack

From the repository root:

```bash
docker compose up -d --build
```

Start only the observability services:

```bash
docker compose up -d prometheus grafana
```

## Access

Prometheus:

```text
http://localhost:9090
```

Grafana:

```text
http://localhost:3000
```

Default local Grafana credentials are controlled by:

```env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-me
```

The password in the real `.env` file should be changed before starting Grafana.

## Dashboard

Grafana automatically provisions:

```text
EuroLedger XRPL / EuroLedger XRPL Worker
```

The dashboard includes:

- current worker health;
- latest persisted XRPL ledger;
- age of the latest successful synchronization;
- successful and failed cycle totals;
- transaction totals by result;
- synchronization freshness over time.

## Prometheus Target

Prometheus scrapes:

```text
http://backend:8000/metrics
```

The target can be inspected in Prometheus under:

```text
Status → Target health
```

The expected job is:

```text
euroledger-xrpl-backend
```

## Useful Commands

Inspect service state:

```bash
docker compose ps
```

Prometheus logs:

```bash
docker compose logs -f prometheus
```

Grafana logs:

```bash
docker compose logs -f grafana
```

Validate the Prometheus configuration:

```bash
docker compose run --rm --no-deps \
  --entrypoint /bin/promtool \
  prometheus \
  check config /etc/prometheus/prometheus.yml
```

Inspect application metrics directly:

```bash
curl -s http://localhost:8000/metrics \
  | grep '^euroledger_'
```

Query Prometheus directly:

```bash
curl -s \
  'http://localhost:9090/api/v1/query?query=euroledger_xrpl_worker_health'
```

## Persistence

Compose volumes:

```text
postgres_data
prometheus_data
grafana_data
```

Stopping the stack does not delete these volumes:

```bash
docker compose down
```

Do not use the following command unless all persistent local data should be deleted:

```bash
docker compose down -v
```

## Security

The observability services are intended for local development.

For a public or shared environment:

- do not expose Prometheus directly to the internet;
- place Grafana behind HTTPS and authentication;
- change the default Grafana password;
- restrict access through a firewall or reverse proxy;
- consider disabling published host ports and exposing services only through an internal network.
