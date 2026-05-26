# EuroLedger XRPL Backend

FastAPI backend for the EuroLedger XRPL proof of concept.

This service will provide the API layer for:

- payment intent creation;
- invoice/payment reference generation;
- XRPL Testnet transaction validation;
- payment status management;
- reconciliation exports.

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

## Current Status

This backend is intentionally minimal.

The first goal is to establish a clean local development environment before adding XRPL Testnet flows, persistence and payment intent logic.

