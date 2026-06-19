# EuroLedger XRPL Backend

FastAPI backend and XRPL payment worker for the EuroLedger XRPL proof of concept.

The backend currently provides:

- payment intent creation and lookup;
- EuroLedger payment reference generation;
- payment intent lifecycle management;
- merchant webhook endpoint management;
- webhook delivery worker support;
- XRPL Testnet transaction retrieval;
- XRPL payment validation and confirmation;
- incremental account synchronization;
- persistent worker cursor management;
- continuous XRPL polling through a separate Compose service.

## Local Development

Run the local development stack from the repository root:

```bash
docker compose up --build
```

The command must be executed from the root directory of the repository, where `docker-compose.yml` is located.

Example:

```bash
cd ~/projects/euroledger-xrpl
docker compose up --build
```

Run the services in the background:

```bash
docker compose up --build -d
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "euroledger-xrpl-backend",
  "environment": "local"
}
```

## API Docs

When the backend is running:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## Quality Checks

Run Ruff linting:

```bash
docker compose exec backend ruff check app tests
```

Check Ruff formatting:

```bash
docker compose exec backend ruff format --check app tests
```

Run the test suite:

```bash
docker compose exec backend pytest
```

## Database Migrations

Create an Alembic migration:

```bash
docker compose exec backend   alembic revision --autogenerate -m "migration message"
```

Apply all pending migrations:

```bash
docker compose exec backend alembic upgrade head
```

## Merchant Webhooks

Merchants can configure webhook endpoints to receive notifications when payment
intents are confirmed, expired or cancelled.

See:

```text
../docs/merchant-webhooks.md
```

## XRPL Worker

The XRPL worker runs as a separate Compose service from the FastAPI backend.

It continuously synchronizes transactions for the configured XRPL Testnet merchant account and reuses the ledger cursor persisted in PostgreSQL.

The worker service executes a command equivalent to:

```text
xrpl-worker --testnet --limit 20 --poll-interval 30
```

The transaction limit and polling interval can be configured through:

```env
XRPL_WORKER_LIMIT=20
XRPL_WORKER_POLL_INTERVAL=30
```

The XRPL merchant address must also be configured:

```env
XRPL_MERCHANT_ADDRESS=r...
```

The XRPL secret or seed is not required for read-only `account_tx` synchronization and must not be committed to the repository.

### Start the Complete Stack

```bash
docker compose up --build
```

Or in the background:

```bash
docker compose up --build -d
```

### Inspect Worker Logs

```bash
docker compose logs -f xrpl-worker
```

Exit log streaming with `Ctrl+C`. This does not stop the worker container.

### Stop and Start Only the Worker

Stop the worker without stopping the API or PostgreSQL:

```bash
docker compose stop xrpl-worker
```

Start it again:

```bash
docker compose start xrpl-worker
```

### Recreate Only the Worker

After changing its configuration or image:

```bash
docker compose up -d --build xrpl-worker
```

### Run Without the Worker

Start only PostgreSQL and the API:

```bash
docker compose up -d postgres backend
```

### One-shot Execution

Run a single Testnet synchronization manually:

```bash
docker compose exec backend   xrpl-worker --testnet --limit 20
```

Run the worker against an offline fixture:

```bash
docker compose exec backend   xrpl-worker --fixtures /app/fixtures/xrpl/empty_transactions.json
```

### Persistent Synchronization Cursor

The worker stores its synchronization state in PostgreSQL using the worker name:

```text
xrpl-payment-worker
```

Inspect the current cursor:

```bash
docker compose exec postgres   psql -U euroledger -d euroledger   -c "select worker_name, last_ledger_index, updated_at from worker_states;"
```

The worker does not expose network ports. It shares the backend image and database while running as an independent process.

## Current Status

The proof of concept currently includes:

- FastAPI and PostgreSQL services;
- SQLAlchemy and Alembic persistence;
- payment intent creation, lookup and lifecycle rules;
- XRPL transaction parsing and validation;
- Testnet `account_tx` pagination;
- persistent incremental synchronization;
- one-shot and continuous polling worker modes;
- Ruff and Pytest quality checks;
- Gitea Actions continuous integration.

The project remains under active development and is not intended for production financial use.
